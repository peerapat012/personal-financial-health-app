from sqlalchemy import text

from app.core.config import get_settings
from app.db import engine


def main() -> None:
    settings = get_settings()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print(f"Database connection OK ({settings.app_env})")


if __name__ == "__main__":
    main()
