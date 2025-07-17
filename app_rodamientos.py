# app_rodamientos.py
# Selector de grasa para rodamientos (UI refinada, instrucción en expander, resultados detallados)

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
A = 0.7   # Constante A
B = 0.23  # Exponente B

# Factores y mínimos
LOAD_FACTORS   = {"Baja":1.0, "Media":1.2, "Alta":1.5}
MIN_VISC_BASE  = {"Baja":20.0, "Media":50.0, "Alta":150.0}
POS_FACTORS    = {"Horizontal":1.0, "Vertical":0.75}
NLGI_THRESHOLDS= [(80,"3"),(160,"2"),(240,"1"),(np.inf,"0")]
THICK_OPTIONS  = ["Complejo de litio","Sulfonato de calcio complejo","Poliurea"]

# Rutas de imágenes para rodamientos
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
    # Viscosidad @40°C (cSt) según A·DN^B
    return A * (DN ** B)

def adjust_for_load(v, carga):
    return v * LOAD_FACTORS[carga]

def select_NLGI(Ks):
    nlg = int(round(Ks))
    return str(max(0, min(3, nlg)))

def select_thickener(amb):
    return "Sulfonato de calcio complejo" if ("Agua" in amb or "Vibración" in amb) else "Complejo de litio"

# =====================
# Función principal
# =====================
def main():
    # Header con logo y creador
    cols = st.columns([1,8], gap="small")
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

    # Imágenes de rodamientos arriba
    with st.expander("Tipos de Rodamientos"):
        cols_imgs = st.columns(len(BEARING_TYPES), gap="small")
        for i, (name, img) in enumerate(BEARING_TYPES.items()):
            if os.path.exists(img):
                cols_imgs[i].image(img, caption=name, use_container_width=True)
            else:
                cols_imgs[i].write(f"Sin imagen: {name}")

    # Instrucciones desplegables
    with st.expander("Instrucciones de Uso"):
        st.write("1. Selecciona el tipo de rodamiento.")
        st.write("2. Ingresa RPM, diámetro interior y exterior, temperatura.")
        st.write("3. Elige carga de trabajo:")
        st.markdown("   - **Baja**: aplicaciones ligeras (ventiladores, baja presión).")
        st.markdown("   - **Media**: uso general (bombas, motores moderados).")
        st.markdown("   - **Alta**: cargas pesadas o vibraciones intensas (prensas).")
        st.write("4. Define posición (Horizontal/Vertical) y ambiente.")
        st.write("5. Haz clic en **Calcular** para ver los resultados paso a paso.")

    # Formulario de entradas
    tipo     = st.selectbox("Tipo de rodamiento", list(BEARING_TYPES.keys()))
    rpm      = st.number_input("Velocidad (RPM)", min_value=1.0, value=1.0, step=1.0)
    d        = st.number_input("Diámetro interior (mm)", min_value=0.1, value=10.0)
    D        = st.number_input("Diámetro exterior (mm)", min_value=0.1, value=400.0)
    temp     = st.number_input("Temperatura (°C)", min_value=-50.0, max_value=200.0, value=60.0)
    carga    = st.selectbox("Carga de trabajo", list(LOAD_FACTORS.keys()))
    posicion = st.selectbox("Posición de montaje", list(POS_FACTORS.keys()))
    ambs     = st.multiselect("Ambiente", ["Agua","Polvo","Alta temperatura","Vibración"])

    # Botón Calcular
    if st.button("Calcular", key="calc"):
        # 1) Diámetro medio
        Dm = calc_Dm(d, D)
        # 2) Factor velocidad
        DN = calc_DN(rpm, Dm)
        # 3) Viscosidad base @40°C
        visc40 = calc_base_viscosity(DN)
        # Umbral mínimo de viscosidad base
        minv = MIN_VISC_BASE[carga]
        if visc40 < minv:
            st.warning(f"Viscosidad base {visc40:.1f} cSt < mínimo {minv} cSt para carga '{carga}'. Ajustando…")
            visc40 = minv
        # 4) Viscosidad ajustada
        visc_corr = adjust_for_load(visc40, carga)
        # 5) Factor de consistencia
        Ks = DN / visc40 if visc40 else 0
        # 6) NLGI
        NLGI = select_NLGI(Ks)
        # 7) Espesante recomendado y alternativo
        esp_rec = select_thickener(ambs)
        esp_alt = [t for t in THICK_OPTIONS if t != esp_rec][0]
        # 8) Intervalo relubricación
        interval = int((2000 / LOAD_FACTORS[carga]) * POS_FACTORS[posicion])

        # Resultados explicados
        st.subheader("Resultados Detallados")
        st.markdown(f"**1. Diámetro medio (Dm):** ({d:.1f}+{D:.1f})/2 = {Dm:.1f} mm")
        st.markdown(f"**2. DN (RPM×Dm):** {rpm:.1f}×{Dm:.1f} = {DN:.1f} mm/min")
        st.markdown(f"**3. Visc. base @40 °C:** 0.7×DN^0.23 = {visc40:.1f} cSt")
        st.markdown(f"**4. Visc. ajustada:** {visc40:.1f}×{LOAD_FACTORS[carga]} = {visc_corr:.1f} cSt")
        st.markdown(f"**5. Ks (DN/visc_base):** {DN:.1f}/{visc40:.1f} = {Ks:.2f}")
        st.markdown(f"**6. NLGI (round Ks):** round({Ks:.2f}) = {NLGI}")
        st.markdown(f"**7. Intervalo relubricación:** 2000/{LOAD_FACTORS[carga]}×{POS_FACTORS[posicion]} = {interval} h")
        st.markdown("**Opciones de espesante:**")
        st.markdown(f"- {esp_rec} (recomendado)")
        st.markdown(f"- {esp_alt} (alternativo)")

if __name__ == "__main__":
    main()

