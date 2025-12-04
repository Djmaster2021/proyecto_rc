# domain/ai_chatbot.py
"""
Chatbot con RAG liviano y opción de IA (Gemini).
- Usa una base de conocimiento local (YAML) y recupera contexto por similitud de tokens.
- Si CHATBOT_IA_ENABLED y GEMINI_API_KEY están configurados, llama a Gemini con el contexto.
- Si falla el modelo o no hay llave, responde con la base local y plantillas seguras.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

import yaml
from django.conf import settings

BASE_DIR = Path(settings.BASE_DIR)  # type: ignore
KNOWLEDGE_PATH = BASE_DIR / "docs" / "chatbot_knowledge.yaml"
CONOCIMIENTO_CARGADO = False


def _tokenizar(texto: str) -> List[str]:
    return [t for t in re.split(r"[\\W_]+", texto.lower()) if t]


@lru_cache(maxsize=1)
def cargar_conocimiento() -> List[Dict[str, str]]:
    global CONOCIMIENTO_CARGADO
    if KNOWLEDGE_PATH.exists():
        try:
            with KNOWLEDGE_PATH.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                CONOCIMIENTO_CARGADO = True
                return [
                    {"title": item.get("title", ""), "answer": item.get("answer", "")}
                    for item in data
                    if isinstance(item, dict)
                ]
        except Exception as exc:
            print(f"[CHATBOT] No se pudo cargar knowledge base: {exc}")
    CONOCIMIENTO_CARGADO = False
    # Fallback mínimo
    return [
        {
            "title": "fallback",
            "answer": "Somos Consultorio Dental RC. Puedo ayudarte con horarios, pagos, penalizaciones y servicios. Si es urgencia, contacta directamente al consultorio.",
        }
    ]


def _rank_contexto(pregunta: str, top_k: int = 3) -> List[str]:
    tokens_q = set(_tokenizar(pregunta))
    if not tokens_q:
        return []

    entries = cargar_conocimiento()
    scored = []
    for entry in entries:
        ans = entry.get("answer", "")
        score = len(tokens_q & set(_tokenizar(ans + " " + entry.get("title", ""))))
        scored.append((score, ans))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Siempre toma al menos el mejor contexto aunque el score sea bajo
    filtrados = [ans for score, ans in scored if ans]
    return filtrados[:top_k] if filtrados else [entries[0]["answer"]]


def _acciones_sugeridas(pregunta: str, lang: str = "es") -> str:
    q = pregunta.lower()
    if lang.startswith("en"):
        if any(k in q for k in ["pay", "payment", "penalty", "fee"]):
            return "Want the steps to pay or check a penalty?"
        if any(k in q for k in ["hour", "schedule", "slot", "book", "appointment"]):
            return "I can guide you to view slots and book/reschedule."
        if any(k in q for k in ["where", "location", "address"]):
            return "I can show you how to get the clinic map."
        return "Need help booking, paying, or checking a penalty?"

    if any(k in q for k in ["pago", "pagar", "penal"]):
        return "¿Quieres que te envíe los pasos para pagar o verificar tu penalización?"
    if any(k in q for k in ["hora", "horario", "agenda", "agendar", "cita"]):
        return "Puedo guiarte para ver horarios y agendar/reprogramar tu cita."
    if any(k in q for k in ["ubicacion", "dónde", "donde", "lugar"]):
        return "Puedo indicarte cómo obtener el mapa de la clínica."
    return "¿Necesitas ayuda para agendar, pagar o revisar tu penalización?"


def _respuesta_local(pregunta: str, lang: str = "es") -> str:
    contextos = _rank_contexto(pregunta, top_k=1)
    cuerpo = (contextos[0].strip() if contextos else "").strip()

    if lang.startswith("en"):
        intro = "Hi, I'm the RC dental assistant."
        cta = _acciones_sugeridas(pregunta, lang="en")
        cierre = "If urgent, call or message the clinic to prioritize you."
    else:
        intro = "Hola, soy el asistente del Consultorio Dental RC."
        cta = _acciones_sugeridas(pregunta, lang="es")
        cierre = "Si es urgencia, llama o escribe al consultorio para priorizarte."

    return " ".join([intro, cuerpo, cta, cierre]).strip()[:400]


def _respuesta_gemini(pregunta: str, contextos: List[str]) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("Sin GEMINI_API_KEY configurada")

    try:
        import google.generativeai as genai
    except Exception as exc:
        raise RuntimeError(f"No se pudo importar google.generativeai: {exc}")

    genai.configure(api_key=api_key)
    model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-1.5-flash")

    prompt = (
        "Eres el asistente del Consultorio Dental Rodolfo Castellón (RC). "
        "Responde breve (máx 80 palabras), en español neutro, sin diagnóstico médico. "
        "Solo usa la información del contexto; si no está, pide contactar al consultorio.\n\n"
        f"Contexto:\n- " + "\n- ".join(contextos) + "\n\n"
        f"Pregunta del usuario: {pregunta}\n\nRespuesta:"
    )

    try:
        model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 160,
                "top_p": 0.9,
                "top_k": 40,
            },
        )
        resp = model.generate_content(prompt)
        texto = (getattr(resp, "text", "") or "").strip()
        if not texto:
            raise RuntimeError("Respuesta vacía")
        return texto
    except Exception as exc:
        raise RuntimeError(f"Gemini error: {exc}")


def responder_chatbot(
    pregunta: str,
    history: List[str] | None = None,
    lang_code: str = "es",
) -> Dict[str, str]:
    """
    Responde usando contexto RAG y opcionalmente historial corto (últimos turnos).
    El historial debe ser seguro y breve; se trunca a ~4 mensajes.
    """
    pregunta = (pregunta or "").strip()
    pregunta = pregunta[:500]  # acotar prompt
    if not pregunta:
        base = "Escribe tu duda y te ayudo con horarios, pagos, penalizaciones o servicios del consultorio RC."
        if lang_code.startswith("en"):
            base = "Type your question and I'll help with schedule, payments, penalties, or services."
        return {"message": base, "source": "local"}

    contextos = _rank_contexto(pregunta, top_k=getattr(settings, "CHATBOT_MAX_CONTEXT", 3))
    history = history or []
    history_ctx = history[-4:] if history else []
    if history_ctx:
        contextos.append("Historial reciente: " + " | ".join(history_ctx))

    if getattr(settings, "CHATBOT_IA_ENABLED", False):
        try:
            payload = {"message": _respuesta_gemini(pregunta, contextos), "source": "ia"}
        except Exception as exc:
            print(f"[CHATBOT] Fallback local por error IA: {exc}")
            payload = {
                "message": _respuesta_local(pregunta, lang=lang_code or "es"),
                "source": "local",
                "source_detail": str(exc)[:180],
            }
    else:
        payload = {"message": _respuesta_local(pregunta, lang=lang_code or "es"), "source": "local"}

    if not CONOCIMIENTO_CARGADO:
        # Señalamos modo básico (sin knowledge base)
        payload.setdefault("source_detail", "kb_basic")
        if lang_code.startswith("en"):
            payload["message"] += " (Basic mode: limited knowledge base loaded.)"
        else:
            payload["message"] += " (Modo básico: base de conocimiento limitada.)"

    return payload
