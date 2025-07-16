# app_rodamientos.py
# Selector de grasa para rodamientos (versión profesional con encabezado ajustado)

import streamlit as st            # Framework para la interfaz web
from fpdf import FPDF             # Para generar PDF de resultados
import numpy as np                # Para cálculos numéricos
import os                         # Para manejo de archivos

# Configuración de la página
st.set_page_config(
    page_title="Selector de Grasa",
    page_icon="🔧",
    layout="wide"
)

# Parámetros de cálculo
A = 0.7  # Constante A de la fórmula de viscosidad
B = 0.23 # Exponente B de la fórmula de viscosidad

# Definición de cargas y montaje
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
LOAD_DESCR = {
    "Baja": "Aplicaciones ligeras (e.g., ventiladores domésticos) sin golpes.",
    "Media": "Uso industrial normal (e.g., bombas) con vibraciones moderadas.",
    "Alta": "Cargas pesadas o continuas vibraciones (e.g., prensas)."
}
pos_factors = {"Horizontal": 1.0, "Vertical (eje arriba)": 0.75, "Vertical (eje abajo)": 0.5}
POS_DESCR = {
    "Horizontal": "Eje horizontal: retención de grasa estándar.",
    "Vertical (eje arriba)": "Posición vertical (eje arriba): posible escurrimiento.",
    "Vertical (eje abajo)": "Posición vertical (eje abajo): mayor pérdida de grasa."
}

# Umbrales NLGI
NLGI_THRESHOLDS = [(80, "3"), (160, "2"), (240, "1"), (np.inf, "0")]

# Tipos de rodamientos e imágenes
BEARING_TYPES = {
    "Bolas": "images/rodamientos_bolas.png",
    "Rodillos": "images/rodamientos_rodillos.png",
    "Cónico": "images/rodamientos_conico.png",
    "Axial": "images/rodamientos_axial.png",
}

# Funciones auxiliares

def calc_Dm(d, D): return (d + D) / 2

def calc_DN(n, Dm): return n * Dm

def calc_base_viscosity(DN): return A * (DN ** B)

def adjust_for_load(visc40, carga): return visc40 * LOAD_FACTORS[carga]

def select_NLGI(DN, visc40):
    Ks = DN / visc40
    for thr, grade in NLGI_THRESHOLDS:
        if Ks <= thr:
            return grade, Ks
    return "2", Ks

def select_thickener(amb):
    return "Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb) else "Complejo de litio"

# Función principal

def main():
    # Encabezado con logo y datos del creador
    cols = st.columns([1, 8])
    if os.path.exists("logo_mobil.png"):
        cols[0].image("logo_mobil.png", width=80)
    header_text = """
# Selector de Grasa para Rodamientos

**Javier Parada**  
Ingeniero de Soporte en Campo
"""
    cols[1].markdown(header_text)
    st.markdown("---")

    # Definiciones de carga y montaje
    with st.expander("Definición de carga de trabajo"):
        for lvl, desc in LOAD_DESCR.items():
            st.write(f"**{lvl}**: {desc}")
    with st.expander("Posición de montaje"):
        for pos, desc in POS_DESCR.items():
            st.write(f"**{pos}**: {desc}")
    with st.expander("Tipos de rodamiento"):
        cols2 = st.columns(len(BEARING_TYPES))
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols2[i].image(img, caption=name, use_container_width=True)
            else:
                cols2[i].write(f"Imagen no disponible: {name}")

    # Entradas de usuario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", 1500.0)
    d        = st.number_input("Diámetro interior (mm)", 50.0)
    D        = st.number_input("Diámetro exterior (mm)", 90.0)
    temp     = st.number_input("Temperatura (°C)", 60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    if st.button("Calcular"):
        Dm        = calc_Dm(d, D)
        DN        = calc_DN(rpm, Dm)
        visc40    = calc_base_viscosity(DN)
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        espesante = select_thickener(ambs)
        bases     = ["Mineral", "Semi-sintética", "Sintética"]
        interval  = int((2000 / LOAD_FACTORS[carga]) * pos_factors[posicion])

        # Mostrar resultados
        st.subheader("Resultados")
        st.write(f"**DN (n·Dm):** {DN:.0f} mm/min")
        st.write(f"**Viscosidad base:** {visc40:.1f} cSt")
        st.write(f"**Viscosidad ajustada:** {visc_corr:.1f} cSt")
        st.write(f"**NLGI:** {NLGI} (Ks={Ks:.1f})")
        st.write(f"**Espesante:** {espesante}")
        st.write(f"**Intervalo relubricación:** {interval} h")
        st.write("**Opciones de aceite base:**")
        for b in bases:
            st.write(f"- {b}")

        # Generar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa - Resumen", ln=True)
        pdf.ln(5)
        for ln in [
            f"Rodamiento: {tipo}",
            f"DN={DN:.0f} mm/min | Temp={temp}°C | Carga={carga}",
            f"Posición={posicion}",
            f"NLGI={NLGI} | Vis ajustada={visc_corr:.1f} cSt",
            f"Espesante={espesante}",
            f"Bases={', '.join(bases)}",
            f"Intervalo={interval} h"
        ]:
            pdf.cell(0, 8, ln, ln=True)
        data = pdf.output(dest="S").encode('latin-1')
        st.download_button("Descargar PDF", data=data,
                           file_name="analisis_grasa.pdf",
                           mime="application/pdf")

if __name__ == "__main__":
    main()

