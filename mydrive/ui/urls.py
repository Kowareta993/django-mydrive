from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

app_name = "ui"
urlpatterns = [
    path("login/", login_view, name="login"),
    # path('login/', LoginView.as_view(), name='login'),
    path("register/", register_view, name="register"),
    path("", drive_view, name="index"),
    path("logout/", logout_view, name="logout"),
    path("folder/<int:pk>/", drive_view, name="folder"),
    path("folder/<int:pk>/create-folder", create_folder_view, name="create_folder"),
    path("create-folder/", create_folder_view, name="create_folder"),
    path("upload-file/", upload_file_view, name="upload_file"),
    path("folder/<int:pk>/upload-file", upload_file_view, name="upload_file"),
    path("file/<int:pk>/download", download_view, name="download_file"),
    path("folder/<int:pk>/download", download_view, name="download_folder"),
    path("folder/<int:pk>/rename", rename_view, name="rename_folder"),
    path("file/<int:pk>/rename", rename_view, name="rename_file"),
    path("folder/<int:pk>/delete", delete_view, name="delete_folder"),
    path("file/<int:pk>/delete", delete_view, name="delete_file"),
    path("folder/<int:pk>/move", move_view, name="move_folder"),
    path("file/<int:pk>/move", move_view, name="move_file"),
    path("file/<int:pk>/copy", copy_file_view, name="copy_file"),
]
