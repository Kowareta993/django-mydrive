from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class FileSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    size = serializers.SerializerMethodField(read_only=True)
    upload_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = File
        fields = ["id", "name", "parent", "file", "owner", "size", "upload_date"]
        read_only_fields = ["owner", "size", "upload_date"]

    def validate_parent(self, value):
        if value and value.owner != self.context["request"].user:
            raise serializers.ValidationError(
                "The parent folder must belong to the authenticated user."
            )
        return value

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def get_size(self, obj):
        if obj.file:
            size = obj.file.size
            if size < 1024:
                return f"{size}B"
            if size < 1024**2:
                return f"{size/1024:.1f}KB"
            if size < 1024**3:
                return f"{size/1024/1024:.1f}MB"
            return f"{size/1024/1024/1024:.1f}GB"
        return 0


class FolderSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Folder
        fields = ["id", "name", "parent", "owner", "created_at"]
        read_only_fields = ["owner", "created_at"]

    def validate_parent(self, value):
        if value and value.owner != self.context["request"].user:
            raise serializers.ValidationError(
                "The parent folder must belong to the authenticated user."
            )
        return value

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class RenameSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=255)


class MoveSerializer(serializers.Serializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate_parent(self, value):
        if value and value.owner != self.context["request"].user:
            raise serializers.ValidationError(
                "The parent folder must belong to the authenticated user."
            )
        return value
