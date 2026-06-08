from django.shortcuts import redirect
from django.contrib import messages
from .utils import fetch_user


def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        user = fetch_user(request)  # Call your `fetch_user` function
        if not user:
            messages.error(request, "Authorization failed!")
            return redirect("ui:login")
        return view_func(request, *args, **kwargs)

    return wrapper
