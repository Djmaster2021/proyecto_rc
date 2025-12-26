"""Middleware utilitario para registrar contexto de host cuando hay excepciones.

Se evita modificar el flujo de errores: solo registra y vuelve a lanzar.
"""

import logging

from django.conf import settings


logger = logging.getLogger("proyecto_rc.requests")


class HostLoggingMiddleware:
    """Loggea host y SITE_BASE_URL cuando ocurre una excepción en la request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            host = "<sin_host>"
            try:
                host = request.get_host()
            except Exception:
                pass
            secure = False
            try:
                secure = request.is_secure()
            except Exception:
                pass
            logger.warning(
                "Excepción en request host=%s site_base=%s secure=%s",
                host,
                getattr(settings, "SITE_BASE_URL", ""),
                secure,
                exc_info=True,
            )
            raise
