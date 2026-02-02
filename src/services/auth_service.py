import bcrypt
import uuid
from models.user import User
from repositories.user_repository import UserRepository

class AuthService:

    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, email, username, password):
        if self.user_repo.get_by_email(email):
            raise ValueError("El usuario ya existe")

        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=password_hash
        )

        self.user_repo.create(user)
        return user

    def login(self, email, password):
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Usuario no encontrado")

        if not bcrypt.checkpw(
            password.encode(),
            user.password_hash.encode()
        ):
            raise ValueError("Credenciales inválidas")

        return user
