import os
import numpy as np
import requests
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY")
EMBEDDING_MODEL = "text-embedding-004"
GENERATIVE_MODEL = "gemini-2.5-flash"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

if not API_KEY:
    raise ValueError("A chave da API do Google não foi encontrada.")

pdf_data_cache = None
system_prompt = None

def load_knowledge_base():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "knowledge_base.json")
    try:
        print(f"Carregando base de conhecimento de: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            item['embedding'] = np.array(item['embedding'])
        print("Base de conhecimento carregada com sucesso.")
        return data
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: Arquivo 'knowledge_base.json' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao carregar ou processar 'knowledge_base.json': {e}")
        return None

def load_system_prompt():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "prompt.md")
    try:
        print(f"Carregando prompt de: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        print("Prompt carregado com sucesso.")
        return prompt
    except Exception as e:
        print(f"ERRO ao carregar 'prompt.md': {e}")
        return None

def find_best_chunks(query, pdf_data, top_k=5):
    if not pdf_data: return []
    url = f"{API_BASE_URL}/{EMBEDDING_MODEL}:embedContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": query}]}, "task_type": "RETRIEVAL_QUERY"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        query_embedding = np.array(response.json()['embedding']['values'])
        pdf_embeddings = np.array([item['embedding'] for item in pdf_data])
        similarities = np.dot(pdf_embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [pdf_data[i] for i in top_indices]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao gerar embedding para a pergunta: {e}")
        return []

@app.route("/")
def index():
    if pdf_data_cache is None or system_prompt is None:
        return render_template("index.html", error=True)
    return render_template("index.html", error=False)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "").strip()
    history = data.get("history", [])

    if not query:
        return jsonify({"error": "A pergunta não pode estar vazia."}), 400
    if pdf_data_cache is None or system_prompt is None:
        return jsonify({"error": "A base de conhecimento ou o prompt não foram carregados."}), 500

    try:
        relevant_chunks = find_best_chunks(query, pdf_data_cache)
        context = "\n\n---\n\n".join([chunk['text'] for chunk in relevant_chunks])

        final_prompt = system_prompt.format(context=context)

        contents = [
            {"role": "user", "parts": [{"text": final_prompt}]},
            {"role": "model", "parts": [{"text": "Entendido. Estou pronta para ajudar os alunos do curso de Sistemas de Informação."}]}
        ]
        
        contents.extend(history)
        
        contents.append({"role": "user", "parts": [{"text": query}]})
        
        url = f"{API_BASE_URL}/{GENERATIVE_MODEL}:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {"contents": contents}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['candidates'][0]['content']['parts'][0]['text']
        
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Ocorreu um erro inesperado no servidor: {e}"}), 500

pdf_data_cache = load_knowledge_base()
system_prompt = load_system_prompt()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)