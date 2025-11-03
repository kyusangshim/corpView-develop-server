# /repository/user_repository.py

from sqlalchemy.orm import Session
from models.user import User

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).get(user_id)

def get_user_by_oauth(db: Session, provider: str, sub: str) -> User | None:
    return (
        db.query(User)
        .filter_by(oauth_provider=provider, oauth_sub=sub)
        .first()
    )

def create_user_from_oauth(db: Session, user_info: dict) -> User:
    new_user = User(
        email=user_info["email"],
        name=user_info.get("name"),
        oauth_provider="google",
        oauth_sub=user_info["sub"],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user