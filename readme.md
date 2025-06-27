# Nátaly AI - Agente de Orientação para BSI

Um chatbot inteligente, baseado no modelo Gemini do Google, especializado em responder perguntas sobre o curso de Bacharelado em Sistemas de Informação do IF Baiano - Campus Guanambi.

![Screenshot da Interface do Chatbot](./assets/screenshots/1.png) 
---

## 📖 Sobre o Projeto

Nátaly AI foi criada para ser uma assistente acadêmica virtual, especialista no curso de Sistemas de Informação. O objetivo é centralizar informações de diversos documentos oficiais (como Projeto Pedagógico do Curso, listas de docentes, horários, etc.) e fornecer respostas rápidas, precisas e em linguagem natural para alunos e interessados no curso.

Este projeto utiliza uma arquitetura **RAG (Retrieval-Augmented Generation)**, onde as perguntas dos usuários são respondidas com base em um contexto extraído de uma base de conhecimento pré-processada, evitando "alucinações" e garantindo que as respostas sejam fiéis aos documentos originais.

---

## ✨ Funcionalidades

-   **Interface de Chat:** Uma interface web limpa e responsiva para interação.
-   **Processamento de Linguagem Natural:** Entende as perguntas dos usuários em português.
-   **Base de Conhecimento Específica:** Treinada exclusivamente com documentos do curso de BSI do IF Baiano.
-   **Persona Definida:** Responde como "Nátaly Ramos", uma agente de orientação acadêmica com tom de voz acolhedor e profissional.
-   **Fluxo de Dados Otimizado:** Utiliza um script para pré-processar os documentos e gerar uma base de conhecimento em JSON, garantindo uma inicialização rápida da aplicação em produção.
-   **Sistema Anti-Alucinação:** O prompt do modelo é instruído a responder apenas com base no contexto fornecido, aumentando a confiabilidade das respostas.

---

## 🛠️ Tecnologias Utilizadas

#### **Backend**
-   **Python 3**
-   **Flask:** Micro-framework web para servir a API e a interface.
-   **Google Gemini API:** Utilizada para geração de embeddings e para a geração de respostas.
-   **pypdf:** Para extração de texto de documentos PDF.
-   **NumPy:** Para cálculos vetoriais de similaridade.
-   **python-dotenv:** Para gerenciamento de variáveis de ambiente locais.

#### **Frontend**
-   **HTML5**
-   **CSS3**
-   **JavaScript:** Para interatividade dinâmica do chat e comunicação com o backend.
-   **Marked.js:** Para renderizar as respostas da IA formatadas em Markdown.

#### **Deploy**
-   **Render.com:** Plataforma de nuvem para hospedagem da aplicação Flask.
-   **Gunicorn:** Servidor WSGI para produção.

---

## 🚀 Como Executar Localmente

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

1.  **Clone o Repositório**
    ```bash
    git clone [https://github.com/hugosb2/bsi-Agent.git](https://github.com/hugosb2/bsi-Agent.git)
    cd seu-repositorio
    ```

2.  **Crie e Ative um Ambiente Virtual**
    ```bash
    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente**
    -   Crie um arquivo chamado `.env` na raiz do projeto.
    -   Dentro dele, adicione sua chave da API do Google:
        ```
        GOOGLE_API_KEY="sua_chave_secreta_aqui"
        ```

5.  **Adicione os Documentos Fonte**
    -   Crie uma pasta chamada `documentos` na raiz do projeto.
    -   Coloque todos os arquivos PDF e MD que servirão como base de conhecimento dentro desta pasta.

6.  **Gere a Base de Conhecimento**
    -   Execute o script de extração. Ele irá ler a pasta `documentos` e criar o arquivo `knowledge_base.json`.
    ```bash
    python extract_content.py
    ```

7.  **Inicie a Aplicação Flask**
    ```bash
    python app.py
    ```
    -   Abra seu navegador e acesse `http://127.0.0.1:5001`.

---

## 🔄 Fluxo de Atualização da Base de Conhecimento

Sempre que precisar adicionar, remover ou atualizar um documento:

1.  Modifique os arquivos na pasta `documentos`.
2.  Execute novamente o script `python extract_content.py` para gerar um novo `knowledge_base.json`.
3.  Faça o commit e o push do arquivo `knowledge_base.json` atualizado para o GitHub:
    ```bash
    git add knowledge_base.json
    git commit -m "docs: atualiza a base de conhecimento"
    git push
    ```

---

## ☁️ Deploy no Render

Este projeto está configurado para deploy contínuo no Render.

1.  Crie um novo "Web Service" no Render e conecte-o a este repositório do GitHub.
2.  Certifique-se que a variável de ambiente `GOOGLE_API_KEY` está configurada no painel de **Environment** do Render.
3.  Qualquer `push` para a branch `main` irá acionar um novo deploy automaticamente.

---

## 👤 Autor

-   **[Hugo Barros]**
-   **GitHub:** [@hugosb2](https://github.com/hugosb2)
-   **LinkedIn:** [Hugo Barros](https://www.linkedin.com/in/hugo-barros-7b764b217/)