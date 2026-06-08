from django.conf import settings
import requests


class APIClient:

    @staticmethod
    def post(endpoint, data=None, files=None, token=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        return requests.post(
            url,
            data=data,
            files=files,
            headers=({"Authorization": f"Token {token}"} if token else {}),
        )

    @staticmethod
    def get(endpoint, params=None, token=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        return requests.get(
            url,
            params=params,
            headers=({"Authorization": f"Token {token}"} if token else {}),
        )

    @staticmethod
    def delete(endpoint, token=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        return requests.delete(
            url,
            headers=({"Authorization": f"Token {token}"} if token else {}),
        )


def fetch_user(request):
    response = APIClient.get("/auth/user/", token=get_token(request))
    if response.status_code == 200:
        return response.json()
    return None


def get_token(request):
    return request.session.get("auth-token", None)


def set_token(request, token):
    request.session["auth-token"] = token
