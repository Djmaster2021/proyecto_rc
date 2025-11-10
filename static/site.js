document.addEventListener('DOMContentLoaded', () => {
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
        navbar?.classList.toggle('is-scrolled', window.scrollY > 20);
    }, { passive: true });

    if (burger && mobilePanel) {
        burger.addEventListener('click', () => {
            const isOpen = mobilePanel.classList.toggle('is-open');
            burger.innerHTML = isOpen ? '<i class="ph-bold ph-x"></i>' : '<i class="ph-bold ph-list"></i>';
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

// --- 3. CHATBOT INTELIGENTE ---
function initChatbot() {
    const el = {
        widget: document.getElementById('rc-chatbot'),
        trigger: document.getElementById('chat-trigger'),
        close: document.getElementById('chat-close'),
        msgs: document.getElementById('chat-messages'),
        form: document.getElementById('chat-form'),
        input: document.getElementById('chat-input')
    };

    if (!el.widget || !el.trigger) return;

    el.trigger.onclick = () => {
        const isHidden = el.widget.classList.toggle('chat-hidden');
        if (!isHidden) setTimeout(() => el.input.focus(), 300);
    };
    el.close.onclick = () => el.widget.classList.add('chat-hidden');

    const addMsg = (text, type, isLoader=false) => {
        const div = document.createElement('div');
        div.className = `chat-msg ${type}`;
        if (isLoader) div.id = 'bot-loader';
        div.innerHTML = isLoader ? '<i class="ph-bold ph-dots-three ph-beat"></i>' : text;
        el.msgs.appendChild(div);
        el.msgs.scrollTop = el.msgs.scrollHeight;
        return div;
    };

    const send = async (text) => {
        if (!text.trim()) return;
        addMsg(text, 'user');
        el.input.value = '';
        const loader = addMsg('', 'bot', true);

        try {
            const res = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: text })
            });
            const data = await res.json();
            loader.remove();
            addMsg(data.respuesta, 'bot');
        } catch (err) {
            loader.remove();
            addMsg('⚠️ Error de conexión. Intenta de nuevo.', 'bot');
        }
    };

    el.form.onsubmit = (e) => { e.preventDefault(); send(el.input.value); };
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.onclick = () => send(btn.dataset.msg);
    });
}