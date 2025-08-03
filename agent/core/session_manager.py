# In agent/core/session_manager.py

class SessionManager:
    """
    Una classe semplice per mantenere lo stato di sessione,
    come il token di autenticazione, durante una conversazione.
    """
    _instance = None

    def __new__(cls):
        # Implementa il pattern Singleton per avere una sola istanza
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.clear()
        return cls._instance

    def set_token(self, token: str):
        self.auth_token = token
        print("🔑 Token di autenticazione salvato nella sessione.")

    def get_token(self) -> str | None:
        return self.auth_token

    def clear(self):
        self.auth_token = None

# Istanza globale che può essere importata ovunque
session_manager = SessionManager()