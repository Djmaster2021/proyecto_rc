document.addEventListener('DOMContentLoaded', () => {
    console.log('site.js cargado ✔');
    initNavbar();
    initScrollReveal();
    initChatbot();
});

// --- 1. NAVBAR & MENÚ MÓVIL ---
function initNavbar() {
    const navbar = document.querySelector('.rc-navbar');
    const burger = document.getElementById('burger');
    const mobilePanel = document.getElementById('mobile-panel');

    window.addEventListener('scroll', () => {
        if (!navbar) return;
        navbar.classList.toggle('is-scrolled', window.scrollY > 20);
    }, { passive: true });

    if (burger && mobilePanel) {
        burger.addEventListener('click', () => {
            const isOpen = mobilePanel.classList.toggle('is-open');
            burger.innerHTML = isOpen
                ? '<i class="ph-bold ph-x"></i>'
                : '<i class="ph-bold ph-list"></i>';
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        mobilePanel.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobilePanel.classList.remove('is-open');
                document.body.style.overflow = '';
                burger.innerHTML = '<i class="ph-bold ph-list"></i>';
            });
        });
    }
}

// --- 2. ANIMACIONES SCROLL ---
function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('in');
        });
    }, { threshold: 0.15 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// --- 3. CHATBOT RC (AJUSTADO A LA API REAL) ---
function initChatbot() {
    const el = {
        widget: document.getElementById('rc-chatbot'),
        trigger: document.getElementById('chat-trigger'),
        close: document.getElementById('chat-close'),
        msgs: document.getElementById('chat-messages'),
        form: document.getElementById('chat-form'),
        input: document.getElementById('chat-input')
    };

    if (!el.widget || !el.trigger || !el.form || !el.input || !el.msgs) {
        console.warn('Chatbot RC: faltan elementos en el DOM.');
        return;
    }

    // Abrir / cerrar widget
    el.trigger.addEventListener('click', () => {
        const isHidden = el.widget.classList.toggle('chat-hidden');
        if (!isHidden) {
            setTimeout(() => el.input.focus(), 300);
        }
    });

    if (el.close) {
        el.close.addEventListener('click', () => {
            el.widget.classList.add('chat-hidden');
        });
    }

    // Utilidad para añadir mensajes
    const addMsg = (text, type, isLoader = false) => {
        const div = document.createElement('div');
        div.className = `chat-msg ${type}`;
        if (isLoader) div.id = 'bot-loader';
        div.innerHTML = isLoader ? '<i class="ph-bold ph-dots-three ph-beat"></i>' : text;
        el.msgs.appendChild(div);
        el.msgs.scrollTop = el.msgs.scrollHeight;
        return div;
    };

    // Enviar mensaje al backend
    const send = async (text) => {
        if (!text.trim()) return;
        addMsg(text, 'user');
        el.input.value = '';
        const loader = addMsg('', 'bot', true);
    
        try {
            const res = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                // 👇 aquí el backend espera "query"
                body: JSON.stringify({ query: text })
            });
    
            const data = await res.json();
            loader.remove();
    
            // 👇 aquí el backend responde con "message"
            const respuesta = data.message ?? 'No pude procesar tu consulta en este momento.';
            addMsg(respuesta, 'bot');
        } catch (err) {
            loader.remove();
            addMsg('⚠️ Error de conexión. Intenta de nuevo.', 'bot');
            console.error(err);
        }
    };
    
    // Envío por formulario
    el.form.addEventListener('submit', (e) => {
        e.preventDefault();
        send(el.input.value);
    });

    // Botones rápidos
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.dataset.msg || '';
            if (!text) return;
            send(text);
        });
    });
}
