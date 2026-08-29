from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://surco:surco@localhost:5432/surco"
    jwt_secret: str = "cambia-esto"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173"
    sag_xlsx_url: str = (
        "https://www.sag.gob.cl/sites/default/files/"
        "Plaguicidas%20Autorizados%20-%20resumen%20al%2001-10-2025.xlsx"
    )
    telegram_bot_token: str = ""

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
