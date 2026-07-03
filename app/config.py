from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str

    app_basic_auth_user: str
    app_basic_auth_password: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
