document.addEventListener('DOMContentLoaded', () => {
    // --- INÍCIO DA LÓGICA DE TROCA DE TEMA ---
    const themeToggle = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    const userPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (theme === 'dark') {
            darkIcon.style.display = 'none';
            lightIcon.style.display = 'block';
        } else {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'block';
        }
    };

    const storedTheme = localStorage.getItem('theme');
    const initialTheme = storedTheme ? storedTheme : (userPrefersDark ? 'dark' : 'light');
    applyTheme(initialTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });
    // --- FIM DA LÓGICA DE TROCA DE TEMA ---


    // --- Código do Chatbot ---
    const form = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;

        appendMessage(query, 'user');
        userInput.value = '';
        
        toggleFormState(true);

        try {
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
            appendMessage(data.response, 'ai');

        } catch (error) {
            console.error('Fetch error:', error);
            appendMessage(`Desculpe, ocorreu um erro ao contatar a assistente: ${error.message}`, 'error');
        } finally {
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

        if (type === 'ai') {
            const avatarImg = document.createElement('img');
            avatarImg.src = "/static/perfil.png"; 
            avatarImg.alt = "Avatar";
            avatarImg.classList.add('avatar');
            messageWrapper.appendChild(avatarImg);
        }

        const textDiv = document.createElement('div');
        textDiv.classList.add('text');

        if (type === 'ai' || type === 'error') {
            textDiv.innerHTML = marked.parse(content);
        } else {
            textDiv.textContent = content;
        }
        
        messageWrapper.appendChild(textDiv);
        
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});