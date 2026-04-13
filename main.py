import requests
import json
import pandas as pd
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente
load_dotenv()

# Lista de chaves para alternância
API_KEYS = [os.getenv("API_KEY_1"), os.getenv("API_KEY_2")]
SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
MATCH_URL = "https://api.apollo.io/api/v1/people/match"

def request_apollo(url, payload):
    """Faz requisições alternando API keys apenas em erro de autenticação/limite."""
    
    last_response = None

    for i, key in enumerate(API_KEYS, start=1):
        if not key:
            continue

        headers = {
            "X-Api-Key": key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            last_response = response

            # Só alterna key em problemas de key
            if response.status_code in [401, 429]:
                print(f"⚠️ Key {i} sem acesso ou limite ({response.status_code}). Tentando próxima...")
                continue

            # Qualquer outro retorno é responsabilidade da API/payload
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            # erro de rede, timeout etc → tenta próxima
            print(f"⚠️ Erro de conexão na key {i}: {e}")
            continue

    # Se nenhuma key funcionou
    if last_response is not None:
        print(f"❌ Nenhuma key disponível. Último status: {last_response.status_code}")
        print("Resposta:", last_response.text)

    return None

def get_contact(job_title, location=None, company=None):
    """Realiza a busca inicial de pessoas no Apollo."""
    payload = {
        "person_titles": [job_title],
        "person_locations": [location] if location else None,
        "organization_names": [company] if company else None,
        "per_page": 1
    }
    
    data = request_apollo(SEARCH_URL, payload)
    return data.get("people", []) if data else []

def dados_enriquecidos(contacts):
    """Enriquece os contatos obtendo e-mails e perfis detalhados."""
    enriched_contacts = []
    # Definimos as colunas padrão para evitar o erro de KeyError se a lista for vazia
    columns = ["name", "job_title", "company", "location", "linkedin_url", "photo_url", "email"]

    for person in contacts:
        # Só montamos o payload com o que existe de fato
        p_id = person.get("id")
        if not p_id:
            continue

        match_payload = {
            "id": p_id,
            "reveal_personal_emails": True,
            "reveal_phone_numbers": True
        }
        
        # Adiciona organização só se existir
        org_name = person.get("organization", {}).get("name")
        if org_name:
            match_payload["organization_name"] = org_name

        match_data = request_apollo(MATCH_URL, match_payload)
        
        # Se a API der erro (422, etc), pulamos para o próximo lead sem travar
        if not match_data or "person" not in match_data:
            continue

        p_enriched = match_data.get("person", {})

        # --- PARSER ---
        name = p_enriched.get("name") or person.get("name") or "N/A"
        city = p_enriched.get("city") or person.get("city") or ""
        country = p_enriched.get("country") or person.get("country") or ""
        location_str = ", ".join([p for p in [city, country] if p]) or "N/A"

        enriched_contacts.append({
            "name": name,
            "job_title": p_enriched.get("title") or person.get("title") or "N/A",
            "company": org_name or "N/A",
            "location": location_str,
            "linkedin_url": p_enriched.get("linkedin_url") or person.get("linkedin_url") or "N/A",
            "photo_url": p_enriched.get("photo_url") or person.get("photo_url") or "",
            "email": p_enriched.get("email") or person.get("email") or "Não encontrado"
        })
        
        print(f"✅ Enriquecido: {name}")

    # Retorna o DataFrame. Se enriched_contacts estiver vazio, ele cria um DF vazio com as colunas certas.
    return pd.DataFrame(enriched_contacts, columns=columns)

if __name__ == "__main__":
    contacts = get_contact("Head of Marketing", "Salvador, Brazil")
    if contacts:
        print(dados_enriquecidos(contacts))