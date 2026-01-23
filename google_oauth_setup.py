from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Rutas basadas en tu estructura de proyecto
BASE_DIR = Path(__file__).resolve().parent
CLIENT_CONFIG = BASE_DIR / "google_credentials" / "credentials.json"
TOKEN_FILE = BASE_DIR / "google_credentials" / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresca el token si ya existe pero está expirado
            creds.refresh(Request())
        else:
            # Flujo normal: abrir navegador para iniciar sesión y aceptar permisos
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_CONFIG),
                SCOPES,
            )
            # Usa un puerto fijo para que el redirect URI pueda registrarse en Google Cloud.
            creds = flow.run_local_server(port=8000)

        # Guardamos el token autorizado
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    print("✅ Token OAuth generado correctamente en:", TOKEN_FILE)


if __name__ == "__main__":
    main()
