# app_rodamientos.py
# Selector de grasa para rodamientos (versión completa y verificada)
# Ahora incluye viscosidad del aceite base @40 °C en mm²/s (cSt) según ASTM D445

import streamlit as st            # Interfaz web
from fpdf import FPDF             # Generación de PDF
import numpy as np                # Cálculos numéricos
import os                         # Gestión de archivos
import glob                       # Búsqueda dinámica de archivos

# =====================
# Configuración de la página (Streamlit)
# =====================
st.set_page_config(
    page_title="Selector de Grasa",
    page_icon="🔧",
    layout="wide"
)

# =====================
# Parámetros de cálculo de viscosidad
# =====================
A = 0.7   # Constante A
B = 0.23  # Exponente B

# =====================
# Definición de cargas de trabajo
# =====================
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
LOAD_DESCR = {
    "Baja":  "Aplicaciones ligeras (e.g., ventiladores domésticos) sin golpes.",
    "Media": "Uso industrial normal (e.g., bombas) con vibraciones moderadas.",
    "Alta":  "Cargas pesadas o vibraciones continuas (e.g., prensas)."
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
NLGI_THRESHOLDS = [
    (80,   "3"),
    (160,  "2"),
    (240,  "1"),
    (np.inf, "0"),
]

# =====================
# Opciones de espesantes
# =====================
THICKENER_OPTIONS = [
    "Complejo de litio",
    "Sulfonato de calcio complejo",
    "Poliurea"
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
    """Diámetro medio (mm)."""
    return (d + D) / 2

def calc_DN(n, Dm):
    """Factor de velocidad DN = RPM × Dm."""
    return n * Dm

def calc_base_viscosity(DN):
    """Viscosidad base @40°C (mm²/s, cSt) según ASTM D445."""
    return A * (DN ** B)

def adjust_for_load(visc40, carga):
    """Viscosidad corregida del aceite base según carga."""
    return visc40 * LOAD_FACTORS[carga]

def select_NLGI(DN, visc40):
    """Determina grado NLGI según Ks = DN / visc40."""
    Ks = DN / visc40
    for threshold, grade in NLGI_THRESHOLDS:
        if Ks <= threshold:
            return grade, Ks
    return "2", Ks

def select_thickener(amb):
    """Recomienda espesante según ambiente."""
    if "Agua" in amb or "Vibración" in amb:
        return "Sulfonato de calcio complejo"
    return "Complejo de litio"

# =====================
# Función principal de la aplicación
# =====================

def main():
    # Encabezado con logo y datos
    cols = st.columns([1, 8], gap="small")
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

    # Secciones de ayuda desplegable
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

    # Entradas de usuario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1500.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=50.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=90.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

        # Calcular y mostrar
    if st.button("Calcular"):
        # Cálculos iniciales
        Dm     = calc_Dm(d, D)
        DN     = calc_DN(rpm, Dm)
        visc40 = calc_base_viscosity(DN)
        # Advertencia si DN muy bajo: viscosidad calculada puede no ser suficiente para alta carga
        if DN < 10000:
            st.warning(f"¡Atención! DN = {DN:.0f} mm/min es bajo; la viscosidad base calculada ({visc40:.1f} mm²/s) puede resultar insuficiente para alta carga.")
        visc_corr = adjust_for_load(visc40, carga)(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        recommended = select_thickener(ambs)
        bases     = ["Mineral", "Semi-sintética", "Sintética"]
        interval  = int((2000 / LOAD_FACTORS[carga]) * pos_factors[posicion])

        # Advertencia si DN bajo
        if note_low_DN:
            st.warning(f"Nota: DN = {DN:.0f} mm/min es bajo. Se aplica viscosidad mínima de {visc40:.1f} mm²/s.")

    if st.button("Calcular"):
        # Cálculos
        Dm        = calc_Dm(d, D)
        DN        = calc_DN(rpm, Dm)
        visc40    = calc_base_viscosity(DN)
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        recommended = select_thickener(ambs)
        bases     = ["Mineral", "Semi-sintética", "Sintética"]
        interval  = int((2000 / LOAD_FACTORS[carga]) * pos_factors[posicion])

        # Mostrar resultados
        st.subheader("Resultados")
        st.write(f"**DN (n·Dm):** {DN:.0f} mm/min")
        st.write(f"**Viscosidad del aceite base @40°C (mm²/s, ASTM D445):** {visc40:.1f}")
        st.write(f"**Viscosidad ajustada:** {visc_corr:.1f} mm²/s")
        st.write(f"**NLGI:** {NLGI} (Ks={Ks:.1f})")
        st.write(f"**Posición de montaje:** {posicion}")
        st.write(f"**Intervalo relubricación:** {interval} h")

        # Espesantes
        st.markdown("**Opciones de espesante (recomendado resaltado):**")
        for t in THICKENER_OPTIONS:
            label = f"- {t}"
            if t == recommended:
                st.markdown(f"<span style='color:green'>{label} (recomendado)</span>", unsafe_allow_html=True)
            else:
                st.write(label)

        # Aceites base
        st.markdown("**Opciones de aceite base:**")
        for b in bases:
            st.write(f"- {b}")

        # Generar informe PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Selección de Grasa - Resumen", ln=True)
        pdf.ln(5)
        pdf.cell(0, 8, f"Rodamiento: {tipo}", ln=True)
        pdf.cell(0, 8, f"DN={DN:.0f} mm/min | Temp={temp}°C | Carga={carga}", ln=True)
        pdf.cell(0, 8, f"Posición: {posicion}", ln=True)
        pdf.cell(0, 8, f"Viscosidad base @40°C: {visc40:.1f} mm²/s", ln=True)
        pdf.cell(0, 8, f"Vis ajustada: {visc_corr:.1f} mm²/s", ln=True)
        pdf.cell(0, 8, f"NLGI={NLGI} (Ks={Ks:.1f})", ln=True)
        pdf.cell(0, 8, f"Espesante recomendado: {recommended}", ln=True)
        others = ', '.join([t for t in THICKENER_OPTIONS if t != recommended])
        pdf.cell(0, 8, f"Otras opciones: {others}", ln=True)
        pdf.cell(0, 8, f"Bases: {', '.join(bases)}", ln=True)
        pdf.cell(0, 8, f"Intervalo: {interval} h", ln=True)
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


