# streamlit_app/utils_streamlit.py

import requests

def call_azure_function(url, user_id, mode="auto", alpha=0.5, threshold=5, top_n=5, source="azure"):
    """
    Envoie une requete POST a l'Azure Function avec les bons parametres.
    Version adaptee pour p10recommandation2025final avec gestion robuste des reponses.
    """

    # Construction du payload avec cast explicite pour eviter les types numpy
    payload = {
        "user_id": int(user_id),
        "mode": str(mode),
        "alpha": float(alpha),
        "threshold": int(threshold),
        "top_n": int(top_n),
        "source": str(source)
    }

    # Header HTTP obligatoire pour que la Function reconnaisse le JSON envoye
    headers = {
        "Content-Type": "application/json"
    }

    print("[DEBUG] Payload envoye a Azure Function :", payload)
    print("[DEBUG] URL appelee :", url)

    try:
        # Requete POST avec en-tetes explicites
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        response.raise_for_status()

        result = response.json()
        print("[DEBUG] Reponse complete Azure :", result)
        
        # Gestion robuste des differents formats de reponse
        if isinstance(result, list):
            # Si on recoit directement une liste de recommandations
            print("[DEBUG] Format liste directe")
            return result
            
        elif isinstance(result, dict):
            # Si c'est un dictionnaire, verifier la presence d'erreurs
            if "error" in result:
                print(f"[ERREUR] Erreur Azure Function : {result['error']}")
                return {"error": result["error"]}
            
            # Structure complete avec body (format attendu)
            if "body" in result and "recommendations" in result["body"]:
                print("[DEBUG] Format avec body.recommendations")
                return result["body"]["recommendations"]
            
            # Structure directe avec recommendations
            elif "recommendations" in result:
                print("[DEBUG] Format avec recommendations direct")
                return result["recommendations"]
            
            # Structure complete retournee telle quelle pour traitement dans Streamlit
            elif "message" in result and "body" in result:
                print("[DEBUG] Format complet avec message + body")
                return result
                
            else:
                print("[WARNING] Structure de reponse inattendue :", result)
                return {"error": "Structure de reponse inattendue"}
                
        else:
            print("[ERROR] Type de reponse non gere :", type(result))
            return {"error": "Type de reponse invalide"}

    except requests.exceptions.Timeout:
        print("[ERREUR] Timeout lors de l'appel Azure")
        return {"error": "Timeout lors de l'appel Azure Function"}
        
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Erreur reseau : {e}")
        return {"error": f"Erreur reseau : {str(e)}"}
        
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue : {e}")
        return {"error": f"Erreur inattendue : {str(e)}"}