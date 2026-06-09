from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.urls import resolve

from api.models import Folder

from .utils import APIClient, get_token, set_token
from .forms import *
from .decorators import *


def login_view(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                response = APIClient.post(
                    "/auth/login",
                    data={
                        "username": form.cleaned_data.get("username"),
                        "password": form.cleaned_data.get("password"),
                    },
                )
                if response.status_code == 200:
                    token = response.json().get("key")
                    set_token(request, token)
                    return redirect("ui:index")
                else:
                    messages.error(request, "Invalid username or password")
            except:
                messages.error(request, "Error in sending request")

    return render(
        request,
        "login.html",
        {"form": form},
    )


def register_view(request):
    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                response = APIClient.post(
                    "/auth/register/",
                    data={
                        "username": form.cleaned_data.get("username"),
                        "email": form.cleaned_data.get("email"),
                        "password1": form.cleaned_data.get("password"),
                        "password2": form.cleaned_data.get("confirm_password"),
                    },
                )
                if response.status_code == 201:
                    messages.success(request, "Registration successful")
                    return redirect("ui:login")
                else:
                    messages.error(
                        request,
                        response.text,
                    )
            except:
                messages.error(request, "Error in sending request")

    return render(
        request,
        "register.html",
        {"form": form},
    )


@user_required
def logout_view(request):
    try:
        APIClient.post(
            "/auth/logout/",
            token=get_token(request),
        )
        set_token(request, "")
        messages.success(request, "You have been logged out.")
        return redirect("ui:login")
    except:
        messages.error(request, "Error in sending request")


@user_required
def drive_view(request, pk=None):
    user = fetch_user(request)
    if not user:
        messages.error(request, "Authorization failed!")
        return redirect("ui:login")
    page = int(request.GET.get("page", 1))
    if (
        pk
        and APIClient.get(f"/folders/{pk}", token=get_token(request)).status_code != 200
    ):
        return HttpResponseNotFound("Not Found!")
    folders = APIClient.get(
        f"/folders/",
        params={"parent": pk, "page": page},
        token=get_token(request),
    ).json()
    files = APIClient.get(
        f"/files/",
        params={"parent": pk, "page": page},
        token=get_token(request),
    ).json()

    has_pre = (
        folders.get("previous", None) != None or files.get("previous", None) != None
    )
    has_next = folders.get("next", None) != None or files.get("next", None) != None

    return render(
        request,
        "folder.html",
        {
            "user": user,
            "folder_id": pk,
            "folders": folders.get("results", []),
            "files": files.get("results", []),
            "path": (
                None
                if not pk
                else APIClient.get(
                    f"/folders/{pk}/path", token=get_token(request)
                ).json()
            ),
            "page": {
                "current": page,
                "has_pre": has_pre,
                "has_next": has_next,
            },
        },
    )


@user_required
def create_folder_view(request, pk=None):
    form = CreateFolderForm()
    if request.method == "POST":
        form = CreateFolderForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            response = APIClient.post(
                f"/folders/",
                data={"name": name, "parent": pk},
                token=get_token(request),
            )
            if response.status_code == 201:
                if not pk:
                    return redirect("ui:index")
                return redirect("ui:folder", pk=pk)
            else:
                messages.error(request, response.text)
    return render(
        request,
        "create.html",
        {
            "form": form,
            "parent_id": pk,
        },
    )


@user_required
def upload_file_view(request, pk=None):
    form = FileUploadForm()
    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            with form_data.file.open() as file:
                response = APIClient.post(
                    "/files/",
                    data={"name": form_data.name, "parent": pk},
                    files={"file": file},
                    token=get_token(request),
                )
                if response.status_code == 201:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "File uploaded successfully.",
                        }
                    )

                else:
                    messages.error(
                        request,
                        response.text,
                    )
    return render(
        request,
        "upload.html",
        {
            "form": form,
            "parent_id": pk,
        },
    )


@user_required
def download_view(request, pk):
    url_name = resolve(request.path).url_name
    api_response = APIClient.get(
        f'/{"files" if url_name == "download_file" else "folders"}/{pk}/download',
        token=get_token(request),
    )
    response = HttpResponse(
        api_response.content,
        content_type=api_response.headers.get(
            "Content-Type", "application/octet-stream"
        ),
    )
    response["Content-Disposition"] = api_response.headers.get(
        "Content-Disposition", ""
    )
    return response


@user_required
def rename_view(request, pk):
    form = RenameForm()
    url_name = resolve(request.path).url_name
    is_file = url_name == "rename_file"
    parent = (
        APIClient.get(
            f"/{'folders' if not is_file else 'files'}/{pk}/",
            token=get_token(request),
        )
        .json()
        .get("parent", None)
    )
    if request.method == "POST":
        form = RenameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
        response = APIClient.post(
            f"/{'folders' if not is_file else 'files'}/{pk}/rename/",
            data={"name": name},
            token=get_token(request),
        )

        if response.status_code == 200:

            if parent:
                return redirect("ui:folder", pk=parent)
            return redirect("ui:index")
        else:
            messages.error(request, response.text)
    return render(
        request,
        "rename.html",
        {
            "form": form,
            "parent_id": parent,
            "is_file": is_file,
        },
    )


@user_required
def delete_view(request, pk):
    url_name = resolve(request.path).url_name
    is_file = url_name == "delete_file"
    parent = (
        APIClient.get(
            f"/{'folders' if not is_file else 'files'}/{pk}/",
            token=get_token(request),
        )
        .json()
        .get("parent", None)
    )
    if request.method == "POST":
        response = APIClient.delete(
            f"/{'folders' if not is_file else 'files'}/{pk}/",
            token=get_token(request),
        )
        if response.status_code == 204:
            if parent:
                return redirect("ui:folder", pk=parent)
            return redirect("ui:index")
        else:
            messages.error(request, response.text)
    return render(
        request,
        "delete.html",
        {
            "parent_id": parent,
        },
    )


@user_required
def move_view(request, pk):
    url_name = resolve(request.path).url_name
    is_file = url_name == "move_file"
    item = File.objects.get(pk=pk) if is_file else Folder.objects.get(pk=pk)
    form = MoveForm(is_file=is_file, item=item)
    if request.method == "POST":
        form = MoveForm(request.POST, is_file=is_file, item=item)
        if form.is_valid():
            parent = form.cleaned_data["parent"]
            response = APIClient.post(
                f'/{"files" if is_file else "folders"}/{pk}/move/',
                data={"parent": parent.id if parent else None},
                token=get_token(request),
            )
            if response.status_code == 200:
                if parent:
                    return redirect("ui:folder", pk=parent.id)
                return redirect("ui:index")
            else:
                messages.error(request, response.text)
    return render(
        request,
        "move.html",
        {
            "form": form,
            "is_file": is_file,
            "parent_id": item.parent.pk if item.parent else None,
            "item_id": pk,
        },
    )


@user_required
def copy_file_view(request, pk):
    if not request.method == "GET":
        return HttpResponseNotFound("Not Found!")
    response = APIClient.post(
        f"/files/{pk}/copy/",
        token=get_token(request),
    )
    parent = (
        APIClient.get(
            f"/files/{pk}/",
            token=get_token(request),
        )
        .json()
        .get("parent", None)
    )
    if response.status_code != 201:
        return HttpResponseBadRequest(response.text)
    if parent:
        return redirect("ui:folder", pk=parent)
    return redirect("ui:index")
