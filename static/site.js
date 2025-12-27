document.addEventListener('DOMContentLoaded', () => {
    console.log('Dentalsys Pro: UI Cargada (Modo Alta Legibilidad) ✔');
    initNavbar();
    initScrollReveal();
    initChatbot();
});

// --- 1. NAVBAR & MENÚ MÓVIL ---
function initNavbar() {
    const navbar = document.querySelector('.rc-navbar');
    const burger = document.getElementById('burger');
    const mobilePanel = document.getElementById('mobile-panel');

    // Efecto de vidrio al bajar
    window.addEventListener('scroll', () => {
        if (!navbar) return;
        navbar.classList.toggle('is-scrolled', window.scrollY > 30);
    }, { passive: true });

    // Abrir menú móvil
    if (burger && mobilePanel) {
        burger.addEventListener('click', () => {
            const isOpen = mobilePanel.classList.toggle('is-open');
            // Cambiar icono entre Hamburguesa y X
            burger.innerHTML = isOpen
                ? '<i class="ph-bold ph-x"></i>'
                : '<i class="ph-bold ph-list"></i>';
            // Bloquear scroll del fondo
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        // Cerrar menú al hacer clic en un enlace
        mobilePanel.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobilePanel.classList.remove('is-open');
                document.body.style.overflow = '';
                burger.innerHTML = '<i class="ph-bold ph-list"></i>';
            });
        });
    }
}

// --- 2. ANIMACIONES SCROLL (Aparición suave) ---
function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                // Dejamos de observar una vez que aparece
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 }); // Se activa al ver el 10% del elemento

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// --- 3. CHATBOT RC (Funcionalidad) ---
function initChatbot() {
    const el = {
        widget: document.getElementById('rc-chatbot'),
        trigger: document.getElementById('chat-trigger'),
        close: document.getElementById('chat-close'),
        msgs: document.getElementById('chat-messages'),
        form: document.getElementById('chat-form'),
        input: document.getElementById('chat-input'),
        quickWrap: document.getElementById('chat-quick-replies')
    };

    if (!el.widget || !el.trigger || !el.form || !el.input || !el.msgs) {
        // Silencioso si no hay chat en esta página
        return;
    }

    // Abrir / cerrar widget con animación
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

    // Función para añadir burbujas de mensaje
    const cleanBotText = (text) => {
        if (!text) return text;
        return text
            .replace(/0\.0\.0\.0:\d+/g, 'consultoriorc.com')
            .replace(/LOCAL:?/gi, '')
            .trim();
    };

    const addMsg = (text, type, isLoader = false) => {
        const div = document.createElement('div');
        div.className = `chat-msg ${type}`;
        if (isLoader) div.id = 'bot-loader';
        const safe = isLoader ? '<i class="ph-bold ph-dots-three ph-beat"></i>' : cleanBotText(text);
        div.innerHTML = safe;
        el.msgs.appendChild(div);
        el.msgs.scrollTop = el.msgs.scrollHeight; // Auto-scroll al fondo
        return div;
    };

    // Lógica de envío al backend (API Django)
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
                // Si usas CSRF token en headers, agrégalo aquí
            },
            body: JSON.stringify({ query: text })
        });

            const data = await res.json().catch(() => ({}));
            loader.remove();

            const respuestas = Array.isArray(data.messages) && data.messages.length
                ? data.messages
                : [data.message ?? (res.ok ? 'No pude procesar tu consulta en este momento.' : '⚠️ Error al conectar. Intenta de nuevo.')];
            respuestas.forEach(msg => addMsg(msg, 'bot'));
        } catch (err) {
            loader.remove();
            addMsg('⚠️ Error de conexión. Intenta de nuevo.', 'bot');
            console.error("Chatbot Error:", err);
        }
    };

    // Construye los botones rápidos a partir de la config (data-quick-replies) o usa defaults
    const hydrateQuickReplies = () => {
        const defaults = [
            { label: 'Agendar', value: 'agendar', icon: '🗓️' },
            { label: 'Horarios', value: 'horarios', icon: '🕒' },
            { label: 'Pagar', value: 'pago', icon: '💳' },
            { label: 'Ubicación', value: 'ubicacion', icon: '📍' },
            { label: 'Precios', value: 'precios', icon: '💲' },
            { label: 'Urgencia', value: 'urgencia', icon: '⏱️' }
        ];

        const rawConfig = el.widget?.dataset.quickReplies || el.quickWrap?.dataset.quickReplies;
        let parsed = null;

        if (rawConfig) {
            try {
                parsed = JSON.parse(rawConfig);
            } catch (err) {
                console.warn('Chatbot: data-quick-replies con formato inválido, usando defaults.', err);
            }
        }

        const replies = (Array.isArray(parsed) && parsed.length ? parsed : defaults)
            .map(item => ({
                label: item.label || item.text || item.value || item.msg,
                value: item.value || item.msg || item.label || item.text,
                icon: item.icon || item.emoji || ''
            }))
            .filter(item => item.label && item.value);

        if (!el.quickWrap) return document.querySelectorAll('.quick-btn');

        el.quickWrap.innerHTML = '';
        replies.forEach(({ label, value, icon }) => {
            const btn = document.createElement('button');
            btn.className = 'quick-btn';
            btn.dataset.msg = value;
            btn.textContent = `${icon ? icon + ' ' : ''}${label}`;
            el.quickWrap.appendChild(btn);
        });

        return el.quickWrap.querySelectorAll('.quick-btn');
    };

    const quickButtons = hydrateQuickReplies();
    
    // Evento Submit del formulario
    el.form.addEventListener('submit', (e) => {
        e.preventDefault();
        send(el.input.value);
    });

    // Eventos para botones de respuesta rápida
    (quickButtons.length ? quickButtons : document.querySelectorAll('.quick-btn')).forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.dataset.msg || btn.innerText;
            if (!text) return;
            send(text);
        });
    });
}
