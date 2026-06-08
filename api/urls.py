from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter


app_name = "api"
router = DefaultRouter()
router.register(r"files", FileViewSet, basename="file")
router.register(r"folders", FolderViewSet, basename="folder")

urlpatterns = [
    path("auth/", include("dj_rest_auth.urls"), name="auth"),
    path(
        "auth/register/",
        include("dj_rest_auth.registration.urls"),
        name="auth-register",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
urlpatterns += router.urls
