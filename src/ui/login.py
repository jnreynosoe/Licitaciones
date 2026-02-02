from services.auth_service import AuthService

auth = AuthService()

def login_view(email, password):
    try:
        user = auth.login(email, password)
        return user
    except ValueError as e:
        return str(e)
