from django.conf import settings
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


class APIClient:

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 10

    @staticmethod
    def post(endpoint, data=None, files=None, token=None, timeout=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        timeout = timeout if timeout is not None else APIClient.DEFAULT_TIMEOUT
        try:
            return requests.post(
                url,
                data=data,
                files=files,
                headers=({"Authorization": f"Token {token}"} if token else {}),
                timeout=timeout,
            )
        except (Timeout, ConnectionError, RequestException) as e:
            # Log the error and return a response-like object or raise
            raise RequestException(f"APIClient.post failed: {e}")

    @staticmethod
    def get(endpoint, params=None, token=None, timeout=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        timeout = timeout if timeout is not None else APIClient.DEFAULT_TIMEOUT
        try:
            return requests.get(
                url,
                params=params,
                headers=({"Authorization": f"Token {token}"} if token else {}),
                timeout=timeout,
            )
        except (Timeout, ConnectionError, RequestException) as e:
            raise RequestException(f"APIClient.get failed: {e}")

    @staticmethod
    def delete(endpoint, token=None, timeout=None):
        url = f"{settings.API_BASE_URL}{endpoint}"
        timeout = timeout if timeout is not None else APIClient.DEFAULT_TIMEOUT
        try:
            return requests.delete(
                url,
                headers=({"Authorization": f"Token {token}"} if token else {}),
                timeout=timeout,
            )
        except (Timeout, ConnectionError, RequestException) as e:
            raise RequestException(f"APIClient.delete failed: {e}")


def fetch_user(request):
    token = get_token(request)
    if not token:
        return None
    
    try:
        response = APIClient.get("/auth/user/", token=token, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except RequestException:
        # Log the error if you have logging configured
        return None


def get_token(request):
    return request.session.get("auth-token", None)


def set_token(request, token):
    request.session["auth-token"] = token