# app_rodamientos.py
# Selector de grasa para rodamientos
# Coloca tus imágenes en la carpeta 'images/' junto al script (GitHub → Add file → Upload files)

import streamlit as st            # Framework para la interfaz web
from fpdf import FPDF             # Para generar PDF de resultados
import numpy as np                # Para cálculos numéricos
import os                         # Para manejo de archivos

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
A = 0.7    # Constante A de la fórmula de viscosidad
B = 0.23   # Exponente B de la fórmula de viscosidad

# =====================
# Definición de cargas de trabajo
# =====================
# Cómo identificar la carga:
# - Baja: Aplicaciones ligeras (ventiladores domésticos, pequeños motores eléctricos sin impacto).
# - Media: Uso general (bombas de agua, motores industriales con carga constante).
# - Alta: Cargas pesadas o impactos (equipos de minería, prensas, grandes compresores).

LOAD_FACTORS = {
    "Baja": 1.0,
    "Media": 1.2,
    "Alta": 1.5,
}

# Descripciones ampliadas de cada nivel de carga
LOAD_DESCR = {
    "Baja": (
        "Aplicaciones ligeras como ventiladores o motores de baja potencia. "
        "Sin golpes ni vibraciones fuertes."
    ),
    "Media": (
        "Uso industrial normal como bombas, compresores o motores con carga moderada. "
        "Puede tener vibraciones ocasionales."
    ),
    "Alta": (
        "Aplicaciones pesadas con impactos o vibraciones continuas, "
        "por ejemplo prensas, equipos de minería o grandes compresores."
    ),
}

# =====================
# Umbrales para grado de consistencia NLGI
# =====================
# Ks = DN / v40, rangos:
#   Ks ≤ 80   → NLGI 3
#   80 < Ks ≤ 160 → NLGI 2
#   160 < Ks ≤ 240 → NLGI 1
#   Ks > 240  → NLGI 0
NLGI_THRESHOLDS = [
    (80,   "3"),
    (160,  "2"),
    (240,  "1"),
    (np.inf, "0"),
]

# =====================
# Tipos de rodamientos y sus imágenes
# =====================
BEARING_TYPES = {
    "Bolas": "images/rodamientos_bolas.png",
    "Rodillos": "images/rodamientos_rodillos.png",
    "Cónico": "images/rodamientos_conico.png",
    "Axial": "images/rodamientos_axial.png",
}

# =====================
# Funciones auxiliares
# =====================

def calc_Dm(d, D): return (d + D) / 2

def calc_DN(n, Dm): return n * Dm

def calc_base_viscosity(DN): return A * (DN ** B)

def adjust_for_load(visc40, carga): return visc40 * LOAD_FACTORS[carga]

def select_NLGI(DN, visc40):
    Ks = DN / visc40
    for threshold, grade in NLGI_THRESHOLDS:
        if Ks <= threshold:
            return grade, Ks
    return "2", Ks

def select_thickener(ambiente):
    if "Agua" in ambiente or "Vibración" in ambiente:
        return "Sulfonato de calcio complejo"
    return "Complejo de litio"

# =====================
# Barra lateral: logo e información
# =====================
if os.path.exists("logo_mobil.png"):
    st.sidebar.image("logo_mobil.png", use_column_width=True)
st.sidebar.markdown("## Creado por Javier Parada")
st.sidebar.markdown("**Empresa: Mobil**")
st.sidebar.markdown("---")
st.sidebar.markdown("### Objetivos de la app:")
st.sidebar.markdown(
    "- Seleccionar la grasa adecuada según parámetros técnicos.\n"
    "- Mostrar tipos de rodamientos y sus dimensiones.\n"
    "- Ofrecer múltiples opciones de aceite base."
)

# =====================
# Función principal de Streamlit
# =====================
def main():
    st.title("Selector de Grasa para Rodamientos")
    st.markdown(
        "Complete los datos y determine la carga usando ejemplos claros."
    )
    st.markdown("---")

    # Instrucciones de uso
    with st.expander("Cómo usar la app"):
        st.write(
            "1. Indique el tipo de rodamiento y sus medidas.\n"
            "2. Estime la carga: consulte los ejemplos en la descripción de cargas.\n"
            "3. Seleccione temperatura, condición de carga y ambiente.\n"
            "4. Haga clic en 'Calcular' para ver recomendaciones y descargar PDF."
        )

    # Explicación de condiciones de carga
    with st.expander("Definición de carga de trabajo"):
        for lvl, desc in LOAD_DESCR.items():
            st.write(f"**{lvl}**: {desc}")

    # Visualización de rodamientos
    with st.expander("Tipos de rodamientos"):
        cols = st.columns(len(BEARING_TYPES))
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols[i].image(img, caption=name, use_column_width=True)
            else:
                cols[i].write(f"Imagen no encontrada: {name}")

    # Entradas del formulario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=0.0, value=1500.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.0, value=50.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.0, value=90.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Condición de carga", list(LOAD_FACTORS.keys()))
    ambiente = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    if st.button("Calcular"):
        Dm        = calc_Dm(d, D)
        DN        = calc_DN(rpm, Dm)
        visc40    = calc_base_viscosity(DN)
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        espesante = select_thickener(ambiente)
        bases     = ["Mineral", "Semi-sintética", "Sintética"]

        st.subheader("Resultados")
        st.write(f"DN (n·Dm): {DN:.0f} mm/min")
        st.write(f"Viscosidad base (v40): {visc40:.1f} cSt")
        st.write(f"Viscosidad ajustada: {visc_corr:.1f} cSt")
        st.write(f"Factor Ks: {Ks:.1f}")
        st.write(f"NLGI recomendado: {NLGI}")
        st.write(f"Espesante: {espesante}")
        st.write("Opciones de aceite base:")
        for b in bases:
            st.write(f"- {b}")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa - Resumen", ln=True)
        pdf.ln(5)
        for line in [
            f"Rodamiento: {tipo}",
            f"DN={DN:.0f} mm/min | v40={visc40:.1f} cSt, ajustada={visc_corr:.1f} cSt",
            f"Ks={Ks:.1f}, NLGI={NLGI} | Espesante={espesante}",
            f"Bases recomendadas: {', '.join(bases)}"
        ]:
            pdf.cell(0, 8, line, ln=True)
        pdf_output = pdf.output(dest="S").encode('latin-1')
        st.download_button(
            "Descargar PDF",
            data=pdf_output,
            file_name="analisis_seleccion_grasa.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
