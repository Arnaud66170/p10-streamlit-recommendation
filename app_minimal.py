import streamlit as st
import requests

st.title("Test minimal P10")
st.write("App déployée avec succès!")

if st.button("Test API"):
    try:
        url = "https://p10recommandationfresh.azurewebsites.net/api/get_recommendations"
        params = {"user_id": 8, "mode": "auto", "top_n": 5}
        headers = {"x-functions-key": st.secrets["AZURE_FUNCTION_KEY"]}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        st.json(response.json())
    except Exception as e:
        st.error(f"Erreur: {e}")