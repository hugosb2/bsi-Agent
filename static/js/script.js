// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;

        // Adiciona a mensagem do usuário à UI
        appendMessage(query, 'user');
        userInput.value = '';
        
        // Desabilita o formulário e mostra o indicador de "digitando"
        toggleFormState(true);

        try {
            // Envia a pergunta para o backend
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            // Adiciona a resposta da IA à UI (renderizando o Markdown)
            appendMessage(data.response, 'ai');

        } catch (error) {
            console.error('Fetch error:', error);
            appendMessage(`Desculpe, ocorreu um erro ao contatar a assistente: ${error.message}`, 'error');
        } finally {
            // Reabilita o formulário
            toggleFormState(false);
        }
    });

    function toggleFormState(isLoading) {
        userInput.disabled = isLoading;
        sendButton.disabled = isLoading;
        loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        if (!isLoading) {
            userInput.focus();
        }
    }

    function appendMessage(content, type) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message', `${type}-message`);

        let innerHTML = '';
        // Adiciona o avatar para mensagens da IA
        if (type === 'ai') {
            innerHTML += `<img src="https://www.ifbaiano.edu.br/unidades/guanambi/wp-content/uploads/sites/4/2023/07/cropped-logo-ifbaiano.png" alt="Avatar" class="avatar">`;
        }

        const textDiv = document.createElement('div');
        textDiv.classList.add('text');

        if (type === 'ai' || type === 'error') {
            // Usa a biblioteca Marked para converter Markdown em HTML
            textDiv.innerHTML = marked.parse(content);
        } else {
            textDiv.textContent = content;
        }
        
        messageWrapper.innerHTML = innerHTML;
        messageWrapper.appendChild(textDiv);
        
        chatBox.appendChild(messageWrapper);
        // Rola para a mensagem mais recente
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});