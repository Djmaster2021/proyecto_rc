// Lógica del Asistente RC (chatbot)

document.addEventListener("DOMContentLoaded", () => {
    console.log("chatbot.js cargado ✔");
  
    const chatContainer = document.getElementById("rc-chatbot");
    const chatTrigger   = document.getElementById("chat-trigger");
    const chatClose     = document.getElementById("chat-close");
  
    const chatForm   = document.getElementById("chat-form");
    const chatInput  = document.getElementById("chat-input");
    const chatBox    = document.getElementById("chat-messages");
    const quickBtns  = document.querySelectorAll(".quick-btn");
  
    // Validación básica de DOM
    if (!chatContainer || !chatTrigger || !chatForm || !chatInput || !chatBox) {
      console.warn("Chatbot RC: faltan elementos requeridos en el DOM.");
      return;
    }
  
    // --- Utilidades ---
  
    function agregarMensaje(texto, tipo = "bot") {
      const burbuja = document.createElement("div");
      burbuja.classList.add("chat-msg", tipo === "bot" ? "bot" : "user");
      burbuja.textContent = texto;
      chatBox.appendChild(burbuja);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  
    async function enviarMensaje(texto) {
      const mensaje = texto.trim();
      if (!mensaje) return;

      // Mostrar mensaje del usuario
      agregarMensaje(mensaje, "user");

      try {
        const resp = await fetch("/api/chatbot/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ query: mensaje }), // la API espera "query"
        });

        const data = await resp.json().catch(() => ({}));
        const respuesta = data.message ?? (resp.ok ? "No pude procesar tu consulta en este momento." : "⚠️ Error al conectar. Intenta de nuevo.");
        agregarMensaje(respuesta, "bot");
      } catch (error) {
        console.error("Error en chatbot:", error);
        agregarMensaje("❌ Error al conectar con el servidor. Intenta de nuevo más tarde.", "bot");
      }
    }
  
    // --- Eventos ---
  
    // Enviar texto escrito
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const texto = chatInput.value;
      chatInput.value = "";
      enviarMensaje(texto);
    });
  
    // Botones rápidos (Horarios, Ubicación, Precios)
    quickBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const texto = btn.getAttribute("data-msg") || "";
        if (!texto) return;
        enviarMensaje(texto);
      });
    });
  
    // Abrir / cerrar chatbot
    chatTrigger.addEventListener("click", () => {
      chatContainer.classList.toggle("chat-hidden");
    });
  
    if (chatClose) {
      chatClose.addEventListener("click", () => {
        chatContainer.classList.add("chat-hidden");
      });
    }
  });
  
