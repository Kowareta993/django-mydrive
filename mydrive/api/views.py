import io
import os
import zipfile
from django.contrib.auth.models import User
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser
from rest_framework import status
from rest_framework.decorators import action
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .permissions import *
from django.shortcuts import get_object_or_404
from django.http import FileResponse, StreamingHttpResponse
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename


class UserViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.all().order_by('-date_joined')
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser, FileUploadParser)
    http_method_names = ["get", "post", "head", "delete"]

    def get_permissions(self):
        if self.action in ["retrieve", "update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user).order_by('-upload_date')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "parent",
                openapi.IN_QUERY,
                description="Filter files by parent folder ID, If null returns root files",
                type=openapi.TYPE_INTEGER,
                required=False,
            )
        ],
        responses={200: FileSerializer(many=True)},
    )
    def list(self, request):
        parent = request.GET.get("parent", None)

        if parent:
            queryset = self.get_queryset().filter(parent_id=parent)
        else:
            queryset = self.get_queryset().filter(parent=None)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = FileSerializer(queryset, many=True)
        return Response(serializer.data)

    
    @action(
        detail=True,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def download(self, request, pk=None):
        file = get_object_or_404(self.get_queryset(), pk=pk)
        response = FileResponse(file.file.open(), as_attachment=True)
        response["Content-Disposition"] = f'attachment; filename="{file.name}"'
        return response

    
    @action(
        detail=True,
        methods=["post"],
        serializer_class=RenameSerializer,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def rename(self, request, pk=None):
        file = self.get_object()
        serializer = RenameSerializer(data=request.data)
        if serializer.is_valid():
            file.name = serializer.validated_data["name"]
            file.save()
            return Response(
                {"success": f"File renamed to {file.name}"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=MoveSerializer,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def move(self, request, pk=None):
        file = self.get_object()
        serializer = MoveSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        if serializer.is_valid():
            new_parent = serializer.validated_data.get("parent", None)
            file.parent = new_parent
            file.save()
            return Response(
                {"success": f"File moved to {file.parent}"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=None,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def copy(self, request, pk=None):
        file = self.get_object()
        new_file = File.objects.create(
            name=f"Copy of {file.name}",
            owner=request.user,
            parent=file.parent,
        )

        path = file.file.path
        with open(path, "rb") as f:
            file_data = ContentFile(f.read())
            new_file.file.save(get_valid_filename(f"copy_{file.name}"), file_data)

        new_file.save()

        return Response(
            {"message": "File copied successfully.", "file_id": new_file.id},
            status=status.HTTP_201_CREATED,
        )


class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    http_method_names = ["get", "post", "head", "delete"]
    parser_classes = (FormParser,)

    def get_permissions(self):
        if self.action in ["retrieve", "update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user).order_by('-created_at')

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "parent",
                openapi.IN_QUERY,
                description="Filter folders by parent folder ID, If null returns root folders",
                type=openapi.TYPE_INTEGER,
                required=False,
            )
        ],
        responses={200: FolderSerializer(many=True)},
    )
    def list(self, request):
        parent = request.GET.get("parent", None)
        if parent:
            queryset = self.get_queryset().filter(parent_id=parent)
        else:
            queryset = self.get_queryset().filter(parent=None)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FolderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = FolderSerializer(queryset, many=True)
        return Response(serializer.data)

    # @action(detail=True, permission_classes=[IsAuthenticated, IsOwner])
    # def subfolders(self, request, pk=None):
    #     folder = get_object_or_404(self.get_queryset(), pk=pk)
    #     serializer = FolderSerializer(folder.subfolders.all(), many=True)
    #     return Response(serializer.data)

    @action(detail=True, permission_classes=[IsAuthenticated, IsOwner])
    def path(self, request, pk=None):
        folder = get_object_or_404(self.get_queryset(), pk=pk)
        parents = [folder]
        while parents[-1].parent:
            parents += [parents[-1].parent]
        serializer = FolderSerializer(parents[::-1], many=True)
        return Response(serializer.data)

    # @action(detail=True, permission_classes=[IsAuthenticated, IsOwner])
    # def files(self, request, pk=None):
    #     folder = get_object_or_404(self.get_queryset(), pk=pk)
    #     serializer = FileSerializer(folder.files.all(), many=True)
    #     return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=RenameSerializer,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def rename(self, request, pk=None):
        folder = self.get_object()
        serializer = RenameSerializer(data=request.data)
        if serializer.is_valid():
            folder.name = serializer.validated_data["name"]
            folder.save()
            return Response(
                {"success": f"Folder renamed to {folder.name}"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=MoveSerializer,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def move(self, request, pk=None):
        folder = self.get_object()
        serializer = MoveSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        if serializer.is_valid():
            new_parent = serializer.validated_data.get("parent", None)
            if new_parent and folder.id == new_parent.id:
                return Response(
                    {"error": "Moving a folder to itself is forbidden"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_parent and folder.has_subfolder(new_parent.id, True):
                return Response(
                    {"error": "Moving a folder to its subfolder is forbidden"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            folder.parent = new_parent
            folder.save()
            return Response(
                {"success": f"Folder moved to {folder.parent}"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def download(self, request, pk=None):
        folder = self.get_object()

        def add_files_to_zip(folder, zipf, path=""):
            for file in folder.files.all():
                with file.file.open() as fbytes:
                    zipf.writestr(
                        os.path.join(path, f"{file.id}_{file.name}"), fbytes.read()
                    )
            for subfolder in folder.subfolders.all():
                add_files_to_zip(
                    subfolder,
                    zipf,
                    path=os.path.join(path, f"{subfolder.id}_{subfolder.name}"),
                )

        try:
            in_memory_zip = io.BytesIO()
            with zipfile.ZipFile(in_memory_zip, mode="w") as zipf:
                # for file in folder.files.all():
                #     with file.file.open() as fbytes:
                #         zipf.writestr(f"{file.id}_{file.name}", fbytes.read())
                add_files_to_zip(folder, zipf)

            in_memory_zip.seek(0)
            response = StreamingHttpResponse(
                in_memory_zip, content_type="application/zip"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{folder.name}.zip"'
            )
            return response
        except Exception as e:
            return Response({"error": f"Error creating zip file: {str(e)}"})


schema_view = get_schema_view(
    openapi.Info(
        title="MyDrive API",
        default_version="v1",
        # description="Test description",
        # terms_of_service="https://www.google.com/policies/terms/",
        # contact=openapi.Contact(email="contact@myapi.local"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
