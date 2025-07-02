# streamlit_app/app.py

import streamlit as st
import pandas as pd
import os
import sys
import json
from pathlib import Path

# === Ajout du chemin vers azure/function_app/src ===
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
function_src_path = os.path.join(project_root, "azure", "function_app", "src")
sys.path.append(function_src_path)

# === Imports internes ===
from loaders import load_df, load_metadata, _get_conn_str, _get_blob_buffer
from utils_streamlit import call_azure_function
from config import AZURE_FUNCTION_URL

print("Chemin ajoute :", function_src_path)

# === Configuration interface ===
st.set_page_config(page_title="Recommandation MyContent", layout="wide")
st.title("Recommandation personnalisée d'articles")
st.sidebar.header("Paramètres de recommandation")

# === Demo rapide ===
if st.sidebar.button("Demo live avec un user préchargé"):
    st.session_state.demo_user = 8  # Utilise un user_id qu'on sait valide

# === Chargement des artefacts utilisateurs / articles depuis Azure ===
st.sidebar.info("Source : **Azure Blob Storage** ☁️")

try:
    with st.spinner("Chargement des données depuis Azure..."):
        df_users = load_df(source="azure", filename="df_light.parquet", container_name="artefacts-fresh")
        df_articles = load_metadata(source="azure", filename="df_articles_light.parquet", container_name="artefacts-fresh")
    st.sidebar.success("✅ Données chargées")
except Exception as e:
    st.error(f"❌ Echec du chargement des données depuis Azure : {e}")
    st.stop()

# === Chargement des user_id valides depuis Azure Blob ===
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_user_ids_from_azure():
    """Charge les user_ids valides depuis Azure Blob avec fallback local"""
    try:
        # Tentative de chargement depuis Azure Blob
        conn_str = _get_conn_str()
        buffer = _get_blob_buffer("artefacts-fresh", "user_ids_valid.json", conn_str)
        user_ids = json.loads(buffer.read().decode('utf-8'))
        st.sidebar.success(f"✅ {len(user_ids)} utilisateurs chargés depuis Azure")
        return user_ids
        
    except Exception as e:
        st.sidebar.warning(f"⚠️ Erreur Azure Blob: {str(e)[:100]}...")
        
        # Fallback vers le fichier local
        user_ids_path = Path(project_root) / "outputs" / "user_ids_valid.json"
        try:
            with open(user_ids_path, "r", encoding="utf-8") as f:
                user_ids = json.load(f)
            st.sidebar.info(f"📁 Fallback local: {len(user_ids)} utilisateurs")
            return user_ids
        except Exception as e2:
            st.sidebar.error(f"❌ Erreur fallback local: {e2}")
            # Valeurs par défaut si tout échoue
            return [8, 96, 330, 397, 452, 1060, 1685, 1926, 1943, 2186]

# Chargement des user_ids
user_ids = load_user_ids_from_azure()

# === Sidebar : Parametres utilisateur ===
selected_user_id = st.sidebar.selectbox(
    "Utilisateur :", 
    options=user_ids, 
    index=0 if "demo_user" not in st.session_state else (
        user_ids.index(st.session_state.demo_user) if st.session_state.demo_user in user_ids else 0
    )
)

mode = st.sidebar.radio("Methode :", ["auto", "cbf", "cf", "hybrid"])
alpha = st.sidebar.slider("Ponderation (alpha)", 0.0, 1.0, 0.7)  # Valeur par défaut cohérente avec Azure Function
threshold = st.sidebar.slider("Seuil historique utilisateur", 1, 20, 5)
top_n = st.sidebar.slider("Nombre d'articles a recommander", 1, 10, 5)

# === Bouton de recommandation ===
if st.sidebar.button("🚀 Obtenir les recommandations"):
    with st.spinner("Appel de l'Azure Function..."):
        try:
            # Appel de l'Azure Function (toujours en mode "azure")
            result = call_azure_function(
                url=AZURE_FUNCTION_URL,
                user_id=selected_user_id,
                mode=mode,
                alpha=alpha,
                threshold=threshold,
                top_n=top_n,
                source="azure"  # Toujours azure
            )
            
            # Gestion robuste des differents formats de reponse
            recommendations = []
            
            if isinstance(result, dict) and "error" in result:
                # Cas d'erreur retourne par utils_streamlit
                st.error(f"❌ Erreur Azure Function : {result['error']}")
                
            elif isinstance(result, list):
                # Liste directe de recommandations
                recommendations = result
                st.success(f"✅ Recommandations pour l'utilisateur {selected_user_id} :")
                
            elif isinstance(result, dict):
                # Format complet avec structure message/body
                if "message" in result and result["message"] == "Succes":
                    if "body" in result and "recommendations" in result["body"]:
                        recommendations = result["body"]["recommendations"]
                        st.success(f"✅ Recommandations pour l'utilisateur {selected_user_id} :")
                    else:
                        st.warning("⚠️ Reponse Azure valide mais sans recommandations")
                        
                elif "recommendations" in result:
                    # Format direct avec recommendations (nouveau format Azure Function)
                    recommendations = result["recommendations"]
                    status = result.get("status", "SUCCESS")
                    if status == "SUCCESS":
                        st.success(f"✅ Recommandations pour l'utilisateur {selected_user_id} :")
                        st.info(f"Mode: {result.get('mode', 'auto')} | Alpha: {result.get('alpha', 0.7)} | Temps: {result.get('execution_time', 'N/A')}")
                    else:
                        st.warning(f"⚠️ Statut: {status}")
                    
                else:
                    st.warning("⚠️ Format de reponse Azure inattendu")
                    st.json(result)  # Affiche la reponse pour debug
                    
            else:
                st.error("❌ Type de reponse Azure non gere")
                st.write("Type recu :", type(result))
                st.json(result)
            
            # Affichage des recommandations si on en a
            if recommendations:
                if len(recommendations) == 0:
                    st.info("ℹ️ Aucune recommandation trouvee pour cet utilisateur")
                else:
                    # Affichage des recommandations avec details
                    st.write(f"**{len(recommendations)} articles recommandés :**")
                    
                    # Création de colonnes pour un affichage plus élégant
                    cols = st.columns(min(len(recommendations), 3))
                    
                    for i, article_id in enumerate(recommendations):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            article_info = df_articles[df_articles["article_id"] == article_id]
                            if not article_info.empty:
                                article_data = article_info.iloc[0]
                                title = article_data.get("title", f"Article {article_id}")
                                category = article_data.get("category_id", "Non specifie")
                                words_count = article_data.get("words_count", "N/A")
                                publisher = article_data.get("publisher_id", "N/A")
                                
                                st.metric(
                                    label=f"#{i+1}",
                                    value=f"Article {article_id}",
                                    delta=f"Cat: {category}"
                                )
                                st.caption(f"📖 {words_count} mots | 🏢 {publisher}")
                            else:
                                st.metric(
                                    label=f"#{i+1}",
                                    value=f"Article {article_id}",
                                    delta="Info non disponible"
                                )
                            
        except Exception as e:
            st.error(f"❌ Erreur lors de l'appel Azure : {e}")
            st.write("Details de l'erreur :", str(e))

# === Affichage des donnees utilisateur ===
if st.checkbox("📊 Afficher l'historique utilisateur"):
    user_history = df_users[df_users["user_id"] == selected_user_id]
    if not user_history.empty:
        st.subheader(f"Historique de l'utilisateur {selected_user_id}")
        
        # Métriques de l'utilisateur
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre de clics", len(user_history))
        with col2:
            st.metric("Articles uniques", user_history["article_id"].nunique())
        with col3:
            sessions = user_history["session_id"].nunique()
            st.metric("Sessions", sessions)
        
        # Affichage des articles cliques
        clicked_articles = user_history["article_id"].unique()
        st.write(f"**Articles consultés ({len(clicked_articles)}) :**")
        
        # Affichage en colonnes pour les articles cliqués
        for i, article_id in enumerate(clicked_articles[:12]):  # Limite à 12 pour l'affichage
            if i % 4 == 0:  # Nouvelle ligne tous les 4 articles
                cols = st.columns(4)
            
            col_idx = i % 4
            with cols[col_idx]:
                article_info = df_articles[df_articles["article_id"] == article_id]
                if not article_info.empty:
                    title = article_info.iloc[0].get("title", f"Article {article_id}")
                    category = article_info.iloc[0].get("category_id", "N/A")
                    st.caption(f"📄 **{article_id}**")
                    st.caption(f"Cat: {category}")
                else:
                    st.caption(f"📄 **{article_id}**")
                    st.caption("Info N/A")
    else:
        st.info("ℹ️ Aucun historique trouve pour cet utilisateur")

# === Informations de debug ===
with st.expander("🔧 Informations techniques"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Utilisateurs valides", len(user_ids))
        st.metric("Lignes dataset", len(df_users))
        st.metric("Articles disponibles", len(df_articles))
    
    with col2:
        st.write(f"**URL Function App :** {AZURE_FUNCTION_URL}")
        st.write(f"**Mode de fonctionnement :** Azure uniquement")
        st.write(f"**Utilisateur sélectionné :** {selected_user_id}")
    
    # Test de connectivité
    if st.button("🧪 Tester la connectivité Azure Function"):
        with st.spinner("Test en cours..."):
            try:
                test_result = call_azure_function(
                    url=AZURE_FUNCTION_URL,
                    user_id=8,  # User ID de test
                    mode="auto",
                    top_n=1
                )
                
                # Gestion des différents types de réponse
                if isinstance(test_result, list) and len(test_result) > 0:
                    st.success("✅ Azure Function accessible et fonctionnelle")
                    st.info(f"Article recommandé: {test_result[0]}")
                elif isinstance(test_result, dict) and "recommendations" in test_result:
                    st.success("✅ Azure Function accessible et fonctionnelle")
                    st.info(f"Recommandations: {test_result['recommendations']}")
                elif isinstance(test_result, dict) and "error" in test_result:
                    st.error(f"❌ Erreur Azure Function: {test_result['error']}")
                else:
                    st.warning("⚠️ Azure Function accessible mais format inattendu")
                    st.json(test_result)
                    
            except Exception as e:
                st.error(f"❌ Erreur de connectivité: {e}")

# === Footer ===
st.markdown("---")
st.markdown("**MyContent Recommendation System** - Powered by Azure Functions ☁️")

# === Instructions de lancement ===
# cd streamlit_app
# streamlit run app.py