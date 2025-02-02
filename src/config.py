from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SANDBOX_API_KEY: str
    LIVE_API_KEY: str
    BOT_TOKEN: str
    ADMINS_LIST: list[int]



    model_config = SettingsConfigDict(env_file="../.env-test")

settings = Settings()