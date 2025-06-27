# app.py
import os
import pypdf
import numpy as np
import requests
import json
from dotenv import load_dotenv
import time
import glob
from flask import Flask, render_template, request, jsonify

# --- 1. CONFIGURAÇÃO INICIAL ---
load_dotenv()

# --- Caminhos ---
# Pega o diretório onde o script está localizado
script_dir = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER_NAME = "documentos"
PDF_FOLDER_PATH = os.path.join(script_dir, PDF_FOLDER_NAME)

# --- Configurações da API Gemini ---
API_KEY = os.getenv("GOOGLE_API_KEY")
EMBEDDING_MODEL = "text-embedding-004"
GENERATIVE_MODEL = "gemini-1.5-flash" # Use o modelo que preferir
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

if not API_KEY:
    raise ValueError("A chave da API do Google não foi encontrada no arquivo .env")

# --- Inicialização do Flask ---
app = Flask(__name__)

# Cache em memória para os dados dos PDFs
pdf_data_cache = None

# --- 2. LÓGICA DE PROCESSAMENTO (Adaptada do original) ---

def process_pdfs_in_folder(folder_path):
    """
    Lê todos os PDFs em uma pasta, gera embeddings e armazena em cache.
    Esta função é chamada uma vez na inicialização do servidor.
    """
    print(f"Iniciando processamento de PDFs em: {folder_path}")
    
    try:
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        if not pdf_files:
            print(f"Nenhum arquivo PDF encontrado em '{folder_path}'.")
            return None
    except Exception as e:
        print(f"ERRO ao acessar o diretório de documentos: {folder_path} | Erro: {e}")
        return None

    all_chunks = []
    for pdf_file_path in pdf_files:
        try:
            filename = os.path.basename(pdf_file_path)
            print(f"Processando: {filename}")
            reader = pypdf.PdfReader(pdf_file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    # Adicionando o número da página à fonte para melhor referência
                    source_info = f"{filename} (página {page_num + 1})"
                    all_chunks.append({"text": text, "source": source_info})
        except Exception as e:
            print(f"Erro ao ler o arquivo {filename}: {e}")
            continue

    if not all_chunks:
        print("Nenhum texto pôde ser extraído dos arquivos PDF.")
        return None

    print(f"Total de {len(all_chunks)} páginas extraídas. Gerando embeddings...")

    all_embeddings = []
    batch_size = 90
    for i in range(0, len(all_chunks), batch_size):
        batch_of_chunks = all_chunks[i:i + batch_size]
        texts_to_embed = [chunk['text'] for chunk in batch_of_chunks]
        
        print(f"  - Processando lote de {len(batch_of_chunks)} chunks...")
        url = f"{API_BASE_URL}/{EMBEDDING_MODEL}:batchEmbedContents?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        requests_payload = {
            "requests": [{"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": text}]}, "task_type": "RETRIEVAL_DOCUMENT"} for text in texts_to_embed]
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(requests_payload))
            response.raise_for_status()
            batch_embeddings = [item['values'] for item in response.json()['embeddings']]
            all_embeddings.extend(batch_embeddings)
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"ERRO DE API! Não foi possível gerar embeddings. Erro: {e}")
            return None

    print("Embeddings gerados com sucesso.")
    return [{"text": chunk['text'], "source": chunk['source'], "embedding": np.array(embedding)} for chunk, embedding in zip(all_chunks, all_embeddings)]

def find_best_chunks(query, pdf_data, top_k=5):
    """
    Encontra os trechos de texto mais relevantes para a pergunta do usuário.
    """
    if not pdf_data: return []
    
    url = f"{API_BASE_URL}/{EMBEDDING_MODEL}:embedContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": query}]}, "task_type": "RETRIEVAL_QUERY"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        query_embedding = np.array(response.json()['embedding']['values'])
        
        # Usando np.dot para performance
        pdf_embeddings = np.array([item['embedding'] for item in pdf_data])
        similarities = np.dot(pdf_embeddings, query_embedding)
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [pdf_data[i] for i in top_indices]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao gerar embedding para a pergunta: {e}")
        return []

# --- 3. ROTAS FLASK ---

@app.route("/")
def index():
    """Renderiza a página principal do chat."""
    # O pdf_data_cache é carregado na inicialização
    if pdf_data_cache is None:
        # Informa ao template que houve um erro no carregamento
        return render_template("index.html", error=True)
    return render_template("index.html", error=False)

@app.route("/ask", methods=["POST"])
def ask():
    """Endpoint para receber a pergunta do usuário e retornar a resposta da IA."""
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "A pergunta não pode estar vazia."}), 400
    
    if pdf_data_cache is None:
        return jsonify({"error": "A base de conhecimento não foi carregada. Verifique os logs do servidor."}), 500

    try:
        # 1. Encontrar chunks relevantes
        relevant_chunks = find_best_chunks(query, pdf_data_cache)
        context = "\n\n---\n\n".join([f"Fonte: {chunk['source']}\nConteúdo: {chunk['text']}" for chunk in relevant_chunks])
        
        # 2. Construir o prompt para o modelo generativo
        prompt = f"""
# Persona e Objetivo
Você é Nátaly Ramos, a Agente de Orientação Acadêmica virtual do IF Baiano. Sua comunicação deve ser sempre clara, acolhedora e humanizada.

# Regras Essenciais
1.  **Base de Conhecimento:** Sua única fonte de informação é o "Contexto fornecido". Para cada informação que usar, cite a fonte original (ex: "segundo o arquivo X.pdf (página Y), ...").
2.  **Aja Naturalmente:** Aja como se soubesse a informação diretamente, mas sempre referencie a fonte quando apresentar dados específicos como horários, locais ou regras.
3.  **Regra Antialucinação:** NUNCA invente horários, professores ou salas se essa informação não estiver no contexto. Se não souber, diga "Não encontrei essa informação nos documentos disponíveis."
4.  **Formatação:** Use Markdown (negrito, listas, etc.) para melhorar a legibilidade.

# Execução
Contexto fornecido:\n---\n{context}\n---\n\nPergunta do usuário:\n{query}

Resposta:
"""
        # 3. Chamar a API Generativa
        url = f"{API_BASE_URL}/{GENERATIVE_MODEL}:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['candidates'][0]['content']['parts'][0]['text']

        return jsonify({"response": ai_response})

    except requests.exceptions.RequestException as err:
        print(f"Erro de API Generativa: {err}")
        return jsonify({"error": f"Ocorreu um erro ao comunicar com a IA: {err}"}), 500
    except (KeyError, IndexError) as err:
        print(f"Erro ao processar resposta da IA: {err}\n{result}")
        return jsonify({"error": "Erro ao processar a resposta da IA."}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": f"Ocorreu um erro inesperado no servidor: {e}"}), 500

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)