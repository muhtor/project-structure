from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.exception import UserDoesNotExist, PasswordIsWrong
from apps.accounts.models import User


class JWTAuth:

    def __init__(self, request):
        self.request = request

    def sos(self):
        return

    @staticmethod
    def check_and_get_user(username: str, password: str) -> User:
        user = User.objects.filter(username=username.strip()).first()

        if not user:
            raise UserDoesNotExist()

        if not user.check_password(password.strip()):
            raise PasswordIsWrong()

        return user

    @staticmethod
    def get_tokens(user: User) -> dict:
        token = RefreshToken.for_user(user)
        return {"access": str(token.access_token), "refresh": str(token)}

    def execute(self):
        data = self.request.data
        user = self.check_and_get_user(username=data['username'], password=data['password'])
        return self.get_tokens(user)
