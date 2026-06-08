from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Folder(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subfolders",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (MyDrive/{self.get_path()})"

    def has_subfolder(self, subfolder_id, recursive=False):
        if self.subfolders.filter(id=subfolder_id).exists():
            return True
        if recursive:
            try:
                subfolder = Folder.objects.get(id=subfolder_id)
            except Folder.DoesNotExist:
                return False
            return self.id in subfolder.get_parent_ids()

    def get_parent_ids(self):
        parent_ids = []
        cur = self
        while cur.parent:
            parent_ids.append(cur.parent.id)
            cur = cur.parent
        return parent_ids

    def get_children_ids(self):
        children_ids = []
        for subfolder in self.subfolders.all():
            children_ids += [subfolder.id] + subfolder.get_children_ids()
        return children_ids

    def get_path(self):
        path = [self.name]
        cur = self
        while cur.parent:
            path += [cur.parent.name]
            cur = cur.parent
        return "/".join(path[::-1])


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    parent = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


@receiver(post_delete, sender=File)
def delete_file_from_filesystem(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
