# app_rodamientos.py
# Selector de grasa para rodamientos usando el método SKF

import streamlit as st            # Framework web para la interfaz
from fpdf import FPDF             # Para generar PDF de resultados
import numpy as np                # Para cálculos numéricos

# =====================
# Constantes y configuraciones SKF
# =====================
A_SKF = 0.7    # Constante A de la fórmula de viscosidad
B_SKF = 0.23   # Exponente B de la fórmula de viscosidad

# Umbrales para grado de consistencia NLGI según Ks = DN / ν40
NLGI_THRESHOLDS = [
    (80,   "3"),
    (160,  "2"),
    (240,  "1"),
    (np.inf, "0"),
]

# Factores de corrección de viscosidad según carga de trabajo
LOAD_FACTORS = {
    "Baja": 1.0,
    "Media": 1.2,
    "Alta": 1.5,
}

# =====================
# Funciones auxiliares
# =====================

def calc_Dm(d, D):
    """Calcula el diámetro medio Dm en mm."""
    return (d + D) / 2


def calc_DN(n, Dm):
    """Calcula DN = velocidad (RPM) × diámetro medio (mm)."""
    return n * Dm


def calc_base_viscosity(DN):
    """Calcula la viscosidad base (cSt @40 °C) usando la fórmula SKF."""
    return A_SKF * (DN ** B_SKF)


def adjust_for_load(visc40, carga):
    """Ajusta la viscosidad base según el nivel de carga."""
    return visc40 * LOAD_FACTORS[carga]


def select_NLGI(DN, visc40):
    """Calcula el factor de consistencia Ks y asigna NLGI según umbrales."""
    Ks = DN / visc40
    for threshold, grade in NLGI_THRESHOLDS:
        if Ks <= threshold:
            return grade, Ks
    return "2", Ks


def select_thickener(ambiente):
    """Elige el tipo de espesante según el ambiente."""
    if "Agua" in ambiente or "Vibración" in ambiente:
        return "Sulfonato de calcio complejo"
    return "Complejo de litio"

# =====================
# Función principal de Streamlit
# =====================

def main():
    st.title("Selector de Grasa para Rodamientos (SKF)")

    # Entradas del usuario
    tipo     = st.selectbox("Tipo de rodamiento", ["Bolas", "Rodillos", "Cónico", "Axial"])
    rpm      = st.number_input("Velocidad (RPM)", min_value=0.0, value=1500.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.0, value=50.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.0, value=90.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Condición de carga", list(LOAD_FACTORS.keys()))
    ambiente = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    # Botón de cálculo
    if st.button("Calcular"):
        # Cálculos SKF
        Dm        = calc_Dm(d, D)
        DN        = calc_DN(rpm, Dm)
        visc40    = calc_base_viscosity(DN)
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        espesante = select_thickener(ambiente)
        base      = "Sintética" if temp > 100 else "Mineral"
        intervalo = int(2000 / LOAD_FACTORS[carga])

        # Mostrar resultados
        st.subheader("Resultados SKF")
        st.write(f"• DN (n·Dm): **{DN:.0f}** mm/min")
        st.write(f"• Viscosidad base ν40: **{visc40:.1f}** cSt")
        st.write(f"• Viscosidad ajustada: **{visc_corr:.1f}** cSt")
        st.write(f"• Factor Ks: **{Ks:.1f}**")
        st.write(f"• NLGI recomendado: **{NLGI}**")
        st.write(f"• Tipo de espesante: **{espesante}**")
        st.write(f"• Tipo de base: **{base}**")
        st.write(f"• Intervalo de relubricación: **{intervalo}** horas")

        # Generar PDF resumen
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa (SKF) - Resumen", ln=True)
        pdf.ln(5)

        lines = [
            f"Rodamiento: {tipo}",
            f"DN={DN:.0f} mm/min",
            f"Viscosidad
