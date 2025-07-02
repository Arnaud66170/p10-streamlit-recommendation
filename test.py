import streamlit as st

st.title("Test ultra minimal P10")
st.write("App déployée avec succès sur Streamlit Cloud!")
st.success("✅ Système fonctionnel")

# Test simple sans secrets
if st.button("Test basique"):
    st.write("Le bouton fonctionne !")
    st.balloons()

st.info("Si tu vois cette page, Streamlit Cloud fonctionne parfaitement.")