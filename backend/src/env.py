import os

from dotenv import load_dotenv

load_dotenv()


def get_env_variable(name: str) -> str:
    """獲取環境變量的值，如果未設置則引發錯誤。"""
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{name}' is not set.")
    return value


ENV = get_env_variable("ENV")
SQL_USER = get_env_variable("SQL_USER")
SQL_PASSWORD = get_env_variable("SQL_PASSWORD")
SQL_HOST = get_env_variable("SQL_HOST")
SQL_PORT = get_env_variable("SQL_PORT")
SQL_DATABASE = get_env_variable("SQL_DATABASE")

JWT_SECRET = get_env_variable("JWT_SECRET")
JWT_EXPIRE_MINUTES = int(get_env_variable("JWT_EXPIRE_MINUTES"))
