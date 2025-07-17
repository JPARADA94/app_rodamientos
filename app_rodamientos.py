# app_rodamientos.py
# Selector de grasa para rodamientos (sin PDF, con explicaciones detalladas)

import streamlit as st
import numpy as np
import os
import glob

# =====================
# Configuración de la página
# =====================
st.set_page_config(
    page_title="Selector de Grasa",
    page_icon="🔧",
    layout="wide"
)

# =====================
# Constantes de cálculo
# =====================
A = 0.7   # Constante A de la fórmula de viscosidad
B = 0.23  # Exponente B de la fórmula de viscosidad

# Factores de carga
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
MIN_VISC_BASE = {"Baja": 20.0, "Media": 50.0, "Alta": 150.0}  # mm²/s mínimo según carga

# Factores de posicionamiento
POS_FACTORS = {"Horizontal": 1.0, "Vertical": 0.75}

# Umbrales NLGI
NLGI_THRESHOLDS = [(80, "3"), (160, "2"), (240, "1"), (np.inf, "0")]

# Opciones de espesante
THICKENER_OPTIONS = ["Complejo de litio", "Sulfonato de calcio complejo", "Poliurea"]

# Rutas de imágenes
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
    """Calcula diámetro medio Dm en mm."""
    return (d + D) / 2


def calc_DN(n, Dm):
    """Calcula factor de velocidad DN = RPM × Dm."""
    return n * Dm


def calc_base_viscosity(DN):
    """Viscosidad base @40°C (mm²/s) según fórmula A·DN^B."""
    return A * (DN ** B)


def adjust_for_load(visc40, carga):
    """Aplica factor de carga a viscosidad base."""
    return visc40 * LOAD_FACTORS[carga]


def select_NLGI(DN, visc40):
    """Determina grado NLGI según Ks = DN/visc40 y umbrales."""
    Ks = DN / visc40
    for thr, grade in NLGI_THRESHOLDS:
        if Ks <= thr:
            return grade, Ks
    return "2", Ks


def select_thickener(amb):
    """Recomienda espesante según presencia de agua o vibración."""
    return ("Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb)
            else "Complejo de litio")

# =====================
# Función principal
# =====================

def main():
    # Header con logo y datos
    cols = st.columns([1, 8], gap="small")
    logos = glob.glob("logo_mobil.*") + glob.glob("images/logo_mobil.*")
    logo = logos[0] if logos else None
    if logo and os.path.exists(logo):
        cols[0].image(logo, width=150)
    else:
        cols[0].write("**Logo no encontrado**")
    cols[1].markdown(
        "# Selector de Grasa para Rodamientos  \n"
        "**Javier Parada**  \nIngeniero de Soporte en Campo",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Inputs del usuario
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=10.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=400.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(POS_FACTORS.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    # Mostrar imágenes de rodamientos
    with st.expander("Tipos de rodamiento"):
        cols2 = st.columns(len(BEARING_TYPES), gap="small")
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols2[i].image(img, caption=name, use_container_width=True)
            else:
                cols2[i].write(f"Imagen no disponible: {name}")

    # Botón calcular
    if st.button("Calcular", key="calc"):
        # Cálculos
        Dm     = calc_Dm(d, D)
        DN     = calc_DN(rpm, Dm)
        visc40 = calc_base_viscosity(DN)
        # Umbral mínimo de viscosidad base
        minv = MIN_VISC_BASE[carga]
        if visc40 < minv:
            st.warning(f"Viscosidad base calculada ({visc40:.1f} cSt) es inferior al mínimo recomendado ({minv} cSt) para carga {carga}.")
            st.info(f"Se ajusta viscosidad base al mínimo recomendado de {minv} cSt para garantizar película adecuada.")
            visc40 = minv
        visc_corr = adjust_for_load(visc40, carga)
        NLGI, Ks  = select_NLGI(DN, visc40)
        esp_rec   = select_thickener(ambs)
        interval  = int((2000 / LOAD_FACTORS[carga]) * POS_FACTORS[posicion])

        # Resultados con explicaciones
        st.subheader("Resultados y Cálculos")
        st.write(f"**Diámetro medio (Dm):** (d + D)/2 = ({d:.1f} + {D:.1f})/2 = {Dm:.1f} mm")
        st.write(f"**Factor de velocidad (DN):** RPM × Dm = {rpm:.1f} × {Dm:.1f} = {DN:.1f} mm/min")
        st.write(f"**Viscosidad base @40 °C:** A × DN^B = {A} × ({DN:.1f}^ {B}) = {visc40:.1f} mm²/s")
        st.write(f"**Viscosidad ajustada por carga:** {visc40:.1f} × {LOAD_FACTORS[carga]} = {visc_corr:.1f} mm²/s")
        st.write(f"**Factor de consistencia (Ks):** DN/visc_base = {DN:.1f}/{visc40:.1f} = {Ks:.2f}")
        st.write(f"**Grado NLGI recomendado:** {NLGI}")
        st.write(f"**Espesante recomendado:** {esp_rec}")
        st.write(f"**Intervalo de relubricación:** {interval} horas")

if __name__ == "__main__":
    main()


