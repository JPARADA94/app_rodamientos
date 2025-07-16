# app_rodamientos.py
# Selector de grasa para rodamientos (con posición de montaje)

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
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
LOAD_DESCR = {
    "Baja": "Aplicaciones ligeras (e.g., ventiladores domésticos) sin golpes.",
    "Media": "Uso industrial normal (e.g., bombas) con vibraciones moderadas.",
    "Alta": "Cargas pesadas o continuas vibraciones (e.g., prensas, maquinaria).",
}

# =====================
# Definición de posiciones de montaje
# =====================
# Esto afecta principalmente al intervalo de relubricación
pos_factors = {
    "Horizontal": 1.0,
    "Vertical (eje arriba)": 0.75,
    "Vertical (eje abajo)": 0.5,
}
POS_DESCR = {
    "Horizontal": "Eje horizontal: retención de grasa estándar.",
    "Vertical (eje arriba)": "Eje vertical con eje arriba: posible escurrimiento.",
    "Vertical (eje abajo)": "Eje vertical con eje abajo: mayor riesgo de pérdida de grasa.",
}

# =====================
# Umbrales NLGI
# =====================
NLGI_THRESHOLDS = [(80, "3"), (160, "2"), (240, "1"), (np.inf, "0")]

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
    for thr, grade in NLGI_THRESHOLDS:
        if Ks <= thr:
            return grade, Ks
    return "2", Ks

def select_thickener(ambiente):
    if "Agua" in ambiente or "Vibración" in ambiente:
        return "Sulfonato de calcio complejo"
    return "Complejo de litio"

# =====================
# Sidebar: logo e información
# =====================
if os.path.exists("logo_mobil.png"):
    st.sidebar.image("logo_mobil.png", use_column_width=True)
st.sidebar.markdown("## Creado por Javier Parada")
st.sidebar.markdown("**Empresa: Mobil**")
st.sidebar.markdown("---")
st.sidebar.markdown("### Objetivos:")
st.sidebar.markdown(
    "- Seleccionar grasa según condiciones reales\n"
    "- Ajustar intervalo según posición de montaje"
)

# =====================
# Función principal de Streamlit
# =====================
def main():
    st.title("Selector de Grasa para Rodamientos")
    st.markdown("Complete los datos y explore las ayudas para carga y posición.")
    st.markdown("---")

    with st.expander("Cómo usar la app"):
        st.write(
            "1. Introduzca medidas y condiciones.\n"
            "2. Consulte definiciones de carga y posición.\n"
            "3. Pulse 'Calcular' para ver resultados y PDF."
        )

    with st.expander("Carga de trabajo"):
        for lvl, desc in LOAD_DESCR.items():
            st.write(f"**{lvl}**: {desc}")

    with st.expander("Posición de montaje"):
        for pos, desc in POS_DESCR.items():
            st.write(f"**{pos}**: {desc}")

    with st.expander("Tipos de rodamientos"):
        cols = st.columns(len(BEARING_TYPES))
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols[i].image(img, caption=name, use_column_width=True)
            else:
                cols[i].write(f"Imagen no encontrada: {name}")

    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", value=1500.0)
    d        = st.number_input("Diámetro interior (mm)", value=50.0)
    D        = st.number_input("Diámetro exterior (mm)", value=90.0)
    temp     = st.number_input("Temperatura (°C)", value=60.0)
    carga    = st.selectbox("Condición de carga", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambiente = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    if st.button("Calcular"):
        Dm        = calc_Dm(d, D)
        DN        = calc_DN(rpm, Dm)
        visc40    = calc_base_viscosity(DN)
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        espesante = select_thickener(ambiente)
        bases     = ["Mineral", "Semi-sintética", "Sintética"]
        interval_base = 2000 / LOAD_FACTORS[carga]
        interval     = int(interval_base * pos_factors[posicion])

        st.subheader("Resultados")
        st.write(f"DN (n·Dm): {DN:.0f} mm/min")
        st.write(f"Viscosidad base: {visc40:.1f} cSt")
        st.write(f"Viscosidad ajustada: {visc_corr:.1f} cSt")
        st.write(f"NLGI: {NLGI} (Ks={Ks:.1f})")
        st.write(f"Espesante: {espesante}")
        st.write(f"Intervalo relubricación: {interval} horas")
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
            f"DN={DN:.0f} mm/min | temp={temp}ºC | carga={carga}",
            f"Posición: {posicion} -> factor retención={pos_factors[posicion]:.2f}",
            f"NLGI={NLGI} | viscosidad ajustada={visc_corr:.1f} cSt",
            f"Espesante={espesante}",
            f"Bases: {', '.join(bases)}",
            f"Intervalo: {interval} h"
        ]:
            pdf.cell(0, 8, line, ln=True)
        out = pdf.output(dest="S").encode('latin-1')
        st.download_button("Descargar PDF", data=out,
                           file_name="analisis_seleccion_grasa.pdf",
                           mime="application/pdf")

if __name__ == "__main__":
    main()


