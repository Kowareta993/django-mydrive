from django import forms
from api.models import *


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Username",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Password",
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Username",
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirm Password",
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ["name", "file"]


class CreateFolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name"]


class RenameForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="New Name",
    )


class MoveForm(forms.Form):
    current = forms.CharField(
        label="Current Item",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    parent = forms.ModelChoiceField(
        queryset=Folder.objects.all(),
        label="Move To",
        empty_label="Root (MyDrive/)",
        widget=forms.Select(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        is_file = kwargs.pop("is_file", None)
        item = kwargs.pop("item", None)
        super().__init__(*args, **kwargs)

        self.fields["current"].label = "File" if is_file else "Folder"

        if item:
            self.fields["current"].initial = item.name
            self.fields["parent"].queryset = Folder.objects.filter(owner=item.owner)
            if not is_file:
                self.fields["parent"].queryset = (
                    self.fields["parent"]
                    .queryset.exclude(id=item.id)
                    .exclude(id__in=item.get_children_ids())
                )
