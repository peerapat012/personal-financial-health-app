import argparse
import getpass
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.core.auth import password_hash
from app.core.config import get_settings
from app.models.auth import AuthOwner


def provision_owner(db: Session, username: str, password: str) -> None:
    username = username.lower()
    if not re.fullmatch(r"[a-z0-9_.]{3,30}", username):
        raise ValueError("Username must be 3-30 letters, numbers, dots, or underscores")
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must be 12-128 characters")
    if db.get(AuthOwner, 1):
        raise ValueError("An owner already exists")
    db.add(AuthOwner(id=1, username=username, password_hash=password_hash.hash(password)))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision the single application owner")
    parser.add_argument("username")
    username = parser.parse_args().username
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")

    engine = create_engine(get_settings().database_direct_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            provision_owner(db, username, password)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except Exception:
        raise SystemExit("Owner provisioning failed; check the database and configuration") from None
    finally:
        engine.dispose()
    print("Owner provisioned")


if __name__ == "__main__":
    main()
