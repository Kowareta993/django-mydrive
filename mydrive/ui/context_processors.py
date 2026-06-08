from .utils import fetch_user


def auth(request):
    return {
        "api_user": fetch_user(request),
    }
