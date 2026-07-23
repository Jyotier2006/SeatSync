from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.errors import ConflictError, UnauthorizedError


class AuthService:
    def __init__(self, users: UserRepository | None = None):
        self.users = users or UserRepository()

    def register(self, db: Session, email: str, full_name: str, password: str) -> User:
        normalized = email.lower().strip()
        if self.users.get_by_email(db, normalized):
            raise ConflictError("An account with this email already exists")
        user = User(
            email=normalized,
            full_name=full_name.strip(),
            password_hash=hash_password(password),
            role=UserRole.CUSTOMER,
        )
        self.users.add(db, user)
        db.commit()
        db.refresh(user)
        return user

    def login(self, db: Session, email: str, password: str) -> tuple[User, str]:
        user = self.users.get_by_email(db, email.lower().strip())
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        token = create_access_token(user.id, user.role.value)
        return user, token
