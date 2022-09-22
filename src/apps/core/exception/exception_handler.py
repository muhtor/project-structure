from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler
from rest_framework.exceptions import ErrorDetail
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import APIException


class BasePosException(APIException):
    def get_full_details(self):
        return {
            "code": self.detail,
            "default_code": self.default_code
        }


class OTPHasBeenSent(BasePosException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("OTP has been sent. Please, wait!")


class UserAlreadyExists(BasePosException):
    status_code = status.HTTP_200_OK
    default_detail =  _("User already exists")


class WrongActivationCode(BasePosException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Wrong otp code")


class ExpiredActivationCode(BasePosException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Expired otp code")


class UserDoesNotExist(BasePosException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("User does not exist")


class PasswordIsWrong(BasePosException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Password is wrong")


class ResetPasswordTokenNotValid(BasePosException):
    status_code = status.HTTP_408_REQUEST_TIMEOUT
    default_detail = _("Reset password token is not valid")


class SuccessResponse:
    def __new__(cls, data=None, text=None, *args, **kwargs):
        return Response({
            "ok": True,
            "text": text,
            "results": data
        }, status=status.HTTP_200_OK)


class ErrorResponse:
    def __new__(cls, text=None, data=None, *args, **kwargs):
        return Response({
            "ok": False,
            "text": text,
            "results": data
        }, status=status.HTTP_400_BAD_REQUEST)


logger = logging.Logger(__name__)


def server_error(request, *args, **kwargs):
    return ErrorResponse(text=_("Server error. Please, contact the developer"))


def status_code_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response
    
    if 400 <= response.status_code <= 499:
        data = response.data

        detail = data.pop("detail", None)
        
        if len(data.keys()) == 0:
            data = None
        
        if data:
            if not detail:
                detail = ""
            for key, value in data.items():
                for error_detail in value:
                    if isinstance(error_detail, ErrorDetail):
                        detail += "'{}' - {} ".format(key, error_detail.lower())
            
            data = None
        
        if detail:
            detail = detail.strip()
        
        status_code = 400
        if response.status_code == 401:
            status_code = 401
        
        response = ErrorResponse(
            text=detail,
            status=status_code
        )
    
    if 200 <= response.status_code <= 299:
        data = response.data
        detail = data.pop("detail", None)
        if not detail:
            data = None
        return SuccessResponse(data=data, status=response.status_code)
    
    return response