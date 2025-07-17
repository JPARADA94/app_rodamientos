# app_rodamientos.py
# Selector de grasa para rodamientos (versión con nota y sin aceite base)

import streamlit as st            # Interfaz web
from fpdf import FPDF             # Generación de PDF
import numpy as np                # Cálculos numéricos
import os                         # Gestión de archivos
import glob                       # Búsqueda dinámica de archivos

# Configuración de la página
st.set_page_config(
    page_title="Selector de Grasa",
    page_icon="🔧",
    layout="wide"
)

# Parámetros de cálculo
A = 0.7   # Constante A
B = 0.23  # Exponente B

# Definición de cargas de trabajo
dcarga = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
descr_carga = {
    "Baja":  "Aplicaciones ligeras (ej: ventiladores domésticos) sin golpes.",
    "Media": "Uso industrial normal (ej: bombas) con vibraciones moderadas.",
    "Alta":  "Cargas pesadas o vibraciones continuas (ej: prensas)."
}
# Viscosidad base mínima recomendada según carga (cSt)
MIN_VISC_BASE = {"Baja": 20.0, "Media": 50.0, "Alta": 150.0}

# Definición de posición de montaje
pos_factors = {"Horizontal": 1.0, "Vertical": 0.75}
descr_pos = {
    "Horizontal": "Eje horizontal: retención estándar de grasa.",
    "Vertical":   "Eje vertical: posible escurrimiento, intervalo ajustado."
}

# Umbrales de consistencia (NLGI)
umbrales_NLGI = [
    (80,   "3"),
    (160,  "2"),
    (240,  "1"),
    (np.inf, "0"),
]

# Opciones de espesantes
THICKENER_OPTIONS = ["Complejo de litio", "Sulfonato de calcio complejo", "Poliurea"]

# Tipos de rodamientos e imágenes
BEARING_TYPES = {
    "Bolas":    "images/rodamientos_bolas.png",
    "Rodillos": "images/rodamientos_rodillos.png",
    "Cónico":   "images/rodamientos_conico.png",
    "Axial":    "images/rodamientos_axial.png",
}

# Funciones auxiliares
def calc_Dm(d, D): return (d + D) / 2
def calc_DN(n, Dm): return n * Dm
def calc_base_viscosity(DN): return A * (DN ** B)
def adjust_for_load(visc40, carga): return visc40 * dcarga[carga]
def select_NLGI(DN, visc40):
    Ks = DN / visc40
    for thr, grade in umbrales_NLGI:
        if Ks <= thr:
            return grade, Ks
    return "2", Ks
def select_thickener(amb):
    return "Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb)
    else "Complejo de litio"

# Función principal
def main():
    cols = st.columns([1, 8], gap="small")
    logos = glob.glob("logo_mobil.*") + glob.glob("images/logo_mobil.*")
    logo = logos[0] if logos else None
    if logo and os.path.exists(logo): cols[0].image(logo, width=150)
    else: cols[0].write("**Logo no encontrado**")
    cols[1].markdown(
        "# Selector de Grasa para Rodamientos  \n"
        "**Javier Parada**  \nIngeniero de Soporte en Campo",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Ayudas desplegables
    with st.expander("Definición de carga de trabajo"):
        for lvl, desc in descr_carga.items(): st.write(f"**{lvl}**: {desc}")
    with st.expander("Posición de montaje"):
        for pos, desc in descr_pos.items(): st.write(f"**{pos}**: {desc}")
    with st.expander("Tipos de rodamiento"):
        cols2 = st.columns(len(BEARING_TYPES), gap="small")
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img): cols2[i].image(img, caption=name, use_container_width=True)
            else: cols2[i].write(f"Imagen no disponible: {name}")

    # Entradas usuario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=10.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=400.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(dcarga.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    if st.button("Calcular", key="calc_button"):
        Dm     = calc_Dm(d, D)
        DN     = calc_DN(rpm, Dm)
        visc40 = calc_base_viscosity(DN)
        # Aplicar umbral mínimo de viscosidad base según carga
        minv = MIN_VISC_BASE[carga]
        if visc40 < minv:
            st.warning(f"Viscosidad base calculada ({visc40:.1f} cSt) inferior al mínimo recomendado ({minv} cSt) para carga {carga}.")
            st.info(f"Se ha ajustado la viscosidad base al mínimo recomendado de {minv} cSt para asegurar película lubricante adecuada.")
            visc40 = minv
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        esp_rec   = select_thickener(ambs)
        interval  = int((2000 / dcarga[carga]) * pos_factors[posicion])

        # Mostrar resultados
        st.subheader("Resultados")
        st.write(f"**DN (n·Dm):** {DN:.0f} mm/min")
        st.write(f"**Viscosidad base @40°C:** {visc40:.1f} cSt (ASTM D445)")
        st.write(f"**Viscosidad ajustada:** {visc_corr:.1f} cSt")
        st.write(f"**NLGI:** {NLGI} (Ks={Ks:.1f})")
        st.write(f"**Espesante recomendado:** {esp_rec}")
        st.write(f"**Opciones de espesante:** {', '.join(THICKENER_OPTIONS)}")
        st.write(f"**Intervalo relubricación:** {interval} h")

        # Generar informe PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa - Resumen", ln=True)
        pdf.ln(5)
        for line in [
            f"Rodamiento: {tipo}",
            f"DN={DN:.0f} mm/min | Temp={temp}°C | Carga={carga}",
            f"Visc.base @40°C={visc40:.1f} cSt | Visc.ajustada={visc_corr:.1f} cSt",
            f"NLGI={NLGI} (Ks={Ks:.1f})", f"Espesante rec.: {esp_rec}",
            f"Espesantes opcionales: {', '.join([t for t in THICKENER_OPTIONS if t != esp_rec])}",
            f"Intervalo: {interval} h"
        ]:
            pdf.cell(0, 8, line, ln=True)
        data = pdf.output(dest="S").encode('latin-1')
        st.download_button("Descargar PDF", data=data, file_name="analisis_grasa.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()

