# app_rodamientos.py
# Selector de grasa para rodamientos (versión con instrucciones y ajuste de NLGI)

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
# Parámetros de cálculo de viscosidad
# =====================
A = 0.7   # Constante A
B = 0.23  # Exponente B

# Factores de carga y mínimo de viscosidad base (cSt)
LOAD_FACTORS = {"Baja": 1.0, "Media": 1.2, "Alta": 1.5}
MIN_VISC_BASE = {"Baja": 20.0, "Media": 50.0, "Alta": 150.0}

# Factores de posición de montaje
pos_factors = {"Horizontal": 1.0, "Vertical": 0.75}

# Opciones de espesante
THICKENER_OPTIONS = ["Complejo de litio", "Sulfonato de calcio complejo", "Poliurea"]

# Rutas de imágenes para tipos de rodamientos
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
    return (d + D) / 2


def calc_DN(n, Dm):
    return n * Dm


def calc_base_viscosity(DN):
    # Viscosidad @40°C (cSt) ASTM D445
    return A * (DN ** B)


def adjust_for_load(visc40, carga):
    return visc40 * LOAD_FACTORS[carga]


def select_NLGI(Ks):
    # Redondeo del factor Ks al entero más cercano, limitado a 0-3
    nlg = int(round(Ks))
    nlg = max(0, min(3, nlg))
    return str(nlg)


def select_thickener(amb):
    # Recomienda espesante según ambiente
    return ("Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb)
            else "Complejo de litio")

# =====================
# Instrucciones de uso
# =====================
st.markdown("""
## Instrucciones de uso:
1. Selecciona el **tipo de rodamiento**.
2. Ingresa las **medidas** (diámetro interior y exterior) y **velocidad (RPM)**.
3. Ajusta la **temperatura**, **carga** (Baja, Media, Alta) y **posición** (Horizontal o Vertical).
4. Define el **ambiente** (agua, polvo, alta temperatura, vibración).
5. Haz clic en **Calcular** para ver los resultados numerados y explicados.
""", unsafe_allow_html=True)

# =====================
# Función principal
# =====================

def main():
    # Encabezado con logo y creador
    cols = st.columns([1, 8], gap="small")
    logo_candidates = glob.glob("logo_mobil.*") + glob.glob("images/logo_mobil.*")
    logo_path = logo_candidates[0] if logo_candidates else None
    if logo_path and os.path.exists(logo_path):
        cols[0].image(logo_path, width=150)
    else:
        cols[0].write("**Logo no encontrado**")
    cols[1].markdown(
        "# Selector de Grasa para Rodamientos  \n"
        "**Javier Parada**  \nIngeniero de Soporte en Campo",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Selección de tipo de rodamiento arriba
    tipo = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))

    # Entradas del formulario
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=10.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=400.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(pos_factors.keys()))
    ambs     = st.multiselect("Ambiente de operación", ["Agua", "Polvo", "Alta temperatura", "Vibración"])

    # Mostrar imágenes de rodamientos
    with st.expander("Visualización de rodamiento seleccionad"):
        img_path = BEARING_TYPES.get(tipo)
        if img_path and os.path.exists(img_path):
            st.image(img_path, caption=tipo, use_container_width=True)
        else:
            st.write("Imagen no disponible para este tipo.")

    # Botón de cálculo
    if st.button("Calcular", key="calc"):
        Dm     = calc_Dm(d, D)
        DN     = calc_DN(rpm, Dm)
        visc40 = calc_base_viscosity(DN)
        # Umbral mínimo
        minv = MIN_VISC_BASE[carga]
        if visc40 < minv:
            st.warning(
                f"1. Viscosidad base calculada ({visc40:.1f} cSt) es inferior al mínimo recomendado ({minv} cSt) para carga '{carga}'."
            )
            st.info(
                f"   Se ajusta viscosidad base a {minv} cSt para garantizar película lubricante."
            )
            visc40 = minv
        visc_corr = adjust_for_load(visc40, carga)
        Ks       = DN / visc40 if visc40 else 0
        NLGI     = select_NLGI(Ks)
        esp_rec  = select_thickener(ambs)
        # Seleccionar segunda opción de espesante
        others = [t for t in THICKENER_OPTIONS if t != esp_rec]
        esp_alt = others[0] if others else ""
        interval = int((2000 / LOAD_FACTORS[carga]) * pos_factors[posicion])

        # Resultados detallados
        st.subheader("Resultados y explicación de cálculos")
        st.write(f"**1. Diámetro medio (Dm):** (d + D)/2 = ({d:.1f} + {D:.1f})/2 = {Dm:.1f} mm")
        st.write(f"**2. Factor de velocidad (DN):** RPM × Dm = {rpm:.1f} × {Dm:.1f} = {DN:.1f} mm/min")
        st.write(f"**3. Viscosidad base @40°C:** A × DN^B = {A} × ({DN:.1f} ^ {B}) = {visc40:.1f} mm²/s")
        st.write(f"**4. Viscosidad ajustada:** viscosidad_base × factor_carga = {visc40:.1f} × {LOAD_FACTORS[carga]} = {visc_corr:.1f} mm²/s")
        st.write(f"**5. Factor de consistencia (Ks):** DN / viscosidad_base = {DN:.1f}/{visc40:.1f} ≈ {Ks:.2f}")
        st.write(f"**6. NLGI (redondeado de Ks):** round({Ks:.2f}) → {NLGI}")
        st.write(f"**7. Intervalo de relubricación:** calculado = 2000/{LOAD_FACTORS[carga]} × factor_posición({posicion}) → {interval} h")
        st.write("**Opciones de espesante:**")
        st.write(f"- {esp_rec} (recomendado)")
        st.write(f"- {esp_alt} (alternativo)")

if __name__ == "__main__":
    main()


