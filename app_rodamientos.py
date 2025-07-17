# app_rodamientos.py
# Selector de grasa para rodamientos (versión completa y verificada)

import streamlit as st            # Framework para la interfaz web
from fpdf import FPDF             # Para generar PDF de resultados
import numpy as np                # Para cálculos numéricos
import os                         # Para manejo de rutas
import glob                       # Para búsqueda dinámica de archivos

# =====================
# Configuración de la página
# =====================
st.set_page_config(
    page_title="Selector de Grasa",
    page_icon="🔧",
    layout="wide"
)

# =====================
# Parámetros de cálculo de viscosidad
# =====================
A = 0.7   # Constante A de la fórmula de viscosidad
B = 0.23  # Exponente B de la fórmula de viscosidad

# =====================
# Definición de cargas de trabajo
# =====================
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
LOAD_DESCR = {
    "Baja":  "Aplicaciones ligeras (e.g., ventiladores domésticos) sin golpes.",
    "Media": "Uso industrial normal (e.g., bombas) con vibraciones moderadas.",
    "Alta":  "Cargas pesadas o continuas vibraciones (e.g., prensas)."
}

# =====================
# Definición de posición de montaje
# =====================
pos_factors = {"Horizontal": 1.0, "Vertical": 0.75}
POS_DESCR = {
    "Horizontal": "Eje horizontal: retención estándar de grasa.",
    "Vertical":   "Eje vertical: posible escurrimiento, intervalo ajustado."
}

# =====================
# Umbrales de consistencia (NLGI)
# =====================
# Ks = DN / v40
NLGI_THRESHOLDS = [
    (80,   "3"),
    (160,  "2"),
    (240,  "1"),
    (np.inf, "0"),
]

# =====================
# Tipos de rodamientos y rutas de imágenes
# =====================
BEARING_TYPES = {
    "Bolas":    "images/rodamientos_bolas.png",
    "Rodillos": "images/rodamientos_rodillos.png",
    "Cónico":   "images/rodamientos_conico.png",
    "Axial":    "images/rodamientos_axial.png",
}

# =====================
# Funciones auxiliares
# =====================

def calc_Dm(d, D):
    """Calcula el diámetro medio Dm (mm)."""
    return (d + D) / 2


def calc_DN(n, Dm):
    """Calcula factor de velocidad DN = RPM × Dm."""
    return n * Dm


def calc_base_viscosity(DN):
    """Calcula la viscosidad base v40 (cSt) usando fórmula A*DN^B."""
    return A * (DN ** B)


def adjust_for_load(visc40, carga):
    """Aplica factor de carga para obtener viscosidad corregida."""
    return visc40 * LOAD_FACTORS[carga]


def select_NLGI(DN, visc40):
    """Determina grado NLGI según Ns = DN/visc40 y umbrales."""
    Ks = DN / visc40
    for threshold, grade in NLGI_THRESHOLDS:
        if Ks <= threshold:
            return grade, Ks
    return "2", Ks


def select_thickener(amb):
    """Elige tipo de espesante según ambiente."""
    return ("Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb)
            else "Complejo de litio")

# =====================
# Función principal de la app
# =====================

def main():
    # Encabezado con logo y datos del creador
    cols = st.columns([1, 8], gap="small")
    # Busca logo en raíz o en images/
    logo_candidates = glob.glob("logo_mobil.*") + glob.glob("images/logo_mobil.*")
    logo_path = logo_candidates[0] if logo_candidates else None
    if logo_path and os.path.exists(logo_path):
        cols[0].image(logo_path, width=150)
    else:
        cols[0].write("**Logo no encontrado**")
    cols[1].markdown(
        "# Selector de Grasa para Rodamientos  \n"
        "**Javier Parada**  \n"
        "Ingeniero de Soporte en Campo",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Ayudas desplegables
    with st.expander("Definición de carga de trabajo"):
        for lvl, desc in LOAD_DESCR.items():
            st.write(f"**{lvl}**: {desc}")

    with st.expander("Posición de montaje"):
        for pos, desc in POS_DESCR.items():
            st.write(f"**{pos}**: {desc}")

    with st.expander("Tipos de rodamiento"):
        cols2 = st.columns(len(BEARING_TYPES), gap="small")
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols2[i].image(img, caption=name, use_container_width=True)
            else:
                cols2[i].write(f"Imagen no disponible: {name}")

    # Entradas del usuario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1500.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=50.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=90.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    # Botón de cálculo
    if st.button("Calcular"):
        # Cálculos
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

        # Generar informe en PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa - Resumen", ln=True)
        pdf.ln(5)
        for line in [
            f"Rodamiento: {tipo}",
            f"DN={DN:.0f} mm/min | Temp={temp}°C | Carga={carga}",
            f"Posición: {posicion}",
            f"NLGI={NLGI} | Vis ajustada={visc_corr:.1f} cSt",
            f"Espesante: {espesante}",
            f"Bases: {', '.join(bases)}",
            f"Intervalo: {interval} h"
        ]:
            pdf.cell(0, 8, line, ln=True)
        data = pdf.output(dest="S").encode('latin-1')
        st.download_button(
            "Descargar PDF",
            data=data,
            file_name="analisis_grasa.pdf",
            mime="application/pdf"
        )

# Punto de entrada
if __name__ == "__main__":
    main()

