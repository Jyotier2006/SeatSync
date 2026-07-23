from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    def get_by_id(self, db: Session, user_id: str) -> User | None:
        return db.get(User, user_id)

    def add(self, db: Session, user: User) -> User:
        db.add(user)
        return user
