import os
import pypdf
import numpy as np
import requests
import json
from dotenv import load_dotenv
import time
import glob

print("--- INICIANDO SCRIPT DE EXTRAÇÃO DE CONTEÚDO ---")

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))
PDF_FOLDER_NAME = "documentos"
PDF_FOLDER_PATH = os.path.join(script_dir, PDF_FOLDER_NAME)
OUTPUT_JSON_PATH = os.path.join(script_dir, "knowledge_base.json")

API_KEY = os.getenv("GOOGLE_API_KEY")
EMBEDDING_MODEL = "text-embedding-004"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

if not API_KEY:
    raise ValueError("A chave da API do Google não foi encontrada no arquivo .env")

def extract_and_embed_pdfs(folder_path):
    print(f"Buscando PDFs em: {folder_path}")
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
                    source_info = f"na lista de docentes do curso (página {page_num + 1})" if "docentes" in filename.lower() else f"no projeto pedagógico do curso (página {page_num + 1})"
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
        requests_payload = {"requests": [{"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": text}]}, "task_type": "RETRIEVAL_DOCUMENT"} for text in texts_to_embed]}
        try:
            response = requests.post(url, headers=headers, data=json.dumps(requests_payload))
            response.raise_for_status()
            batch_embeddings = [item['values'] for item in response.json()['embeddings']]
            all_embeddings.extend(batch_embeddings)
            print("  - Lote processado com sucesso.")
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"ERRO DE API! Não foi possível gerar embeddings. Erro: {e}")
            return None

    print("Embeddings gerados com sucesso.")
    return [{"text": chunk['text'], "source": chunk['source'], "embedding": embedding} for chunk, embedding in zip(all_chunks, all_embeddings)]

if __name__ == "__main__":
    processed_data = extract_and_embed_pdfs(PDF_FOLDER_PATH)
    if processed_data:
        try:
            with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=4)
            print(f"\nSUCESSO! Base de conhecimento salva em '{OUTPUT_JSON_PATH}'")
        except Exception as e:
            print(f"\nERRO ao salvar o arquivo JSON: {e}")