from typing import Any, Optional
from django import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from .models import AuthenticationCode, Video
from django.contrib.auth import get_user_model, authenticate
from django.utils.text import capfirst
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()

class EmailForm(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        user = User.objects.filter(email=email)
        if user.exists():
            raise ValidationError("このメールアドレスは既に使われています。")
        return email
    
    class Meta:
        model = User
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form", "placeholder": "メールアドレス"})
        }

class RegistrationCodeForm(forms.ModelForm):
    def __init__(self, email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email

    def clean_code(self):
        input_code = self.cleaned_data["code"]
        print(input_code)
        print(self.email)
        authentication_code_obj = get_object_or_404(
            AuthenticationCode, email=self.email
        )
        authentication_code = authentication_code_obj.code
        elapased_time = timezone.now() - authentication_code_obj.Uploaded_at
        if elapased_time.seconds > 30:
            raise ValidationError("この認証コードは無効です。新しい認証コードを発行してください。")
        if input_code != authentication_code:
            raise ValidationError("認証コードが正しくありません。")
        return input_code

    class Meta:
        model = AuthenticationCode
        fields = ("code",)
        widgets = {
            "code": forms.TextInput(
                attrs={"class": "form", "placeholder": "認証コード(数字4ケタ)"}
            )
        }

class PasswordForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("password",)
        widgets = {
            "password": forms.PasswordInput(
                attrs={"placeholder": "パスワード", "class": "form"}
            )
        }

class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"autofocus": True, "placeholder": "メールアドレス", "class": "form"}
        ),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput({"placeholder": "パスワード", "class": "form"}),
    )
    error_messages = {
        "invalid_login": "Eメールアドレスまたはパスワードに誤りがあります。",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self.email_field = User._meta.get_field("email")

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache

class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"autofocus": True, "placeholder": "メールアドレス", "class": "form"}
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        user = User.objects.filter(email=email)
        if not user.exists():
            raise ValidationError("このメールアドレスを使用しているユーザーは存在しません。")
        return email    

class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput({"placeholder": "新しいパスワード", "class": "form"})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput({"placeholder": "新しいパスワード(確認)", "class": "form"})
    )

    def clean(self):
        new_password1 = self.cleaned_data["new_password1"]
        new_password2 = self.cleaned_data["new_password2"]
        if new_password1 != new_password2:
            raise ValidationError("パスワードが一致しません")
        return self.cleaned_data
    
class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ("title", "description", "thumbnail", "video")
        widgets = {
            "thumbnail": forms.FileInput(attrs={"class": "thumbnail-form"}),
            "title": forms.Textarea(
                attrs={
                    "class": "title-form",
                    "placeholder": "タイトルを入力",
                    "rows": "2",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "description-form",
                    "placeholder": "詳細文を入力",
                }
            ),
            "video": forms.FileInput(
                attrs={
                    "class": "video-form",
                    "accept": "video/*",
                    "id": "video-upload-btn",
                }
            ),
        }
    
class VideoSearchForm(forms.Form):
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "動画を検索", "class": "search-form"}),
    )

class ViewsCountForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ("views_count",)

# class AccountForm(forms.Form):
#     class Meta:
#         model = User

class PasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs["class"] = "old_password"
        self.fields["new_password1"].widget.attrs["class"] = "new_password1"
        self.fields["new_password2"].widget.attrs["class"] = "new_password2"
        self.fields["old_password"].widget.attrs["placeholder"] = "現在のパスワード"
        self.fields["new_password1"].widget.attrs["placeholder"] = "新しいパスワード"
        self.fields["new_password2"].widget.attrs["placeholder"] = "新しいパスワード（確認）"

class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("icon", "username", "profile")
        labels = {
            "username": "ユーザー名",
            "profile": "紹介文",
        }
        widgets = {"icon": forms.FileInput(attrs={"onchange": "previewImage(this);"}),
                   "username": forms.TextInput(
                attrs={"onkeyup": "showUsernameLength(value);"}
            ),
            "profile": forms.TextInput(attrs={"onkeyup": "showProfileLength(value);"}),
        }


class VideoUpdateForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ("thumbnail", "title", "description")
        widgets = {
            "thumbnail": forms.FileInput(attrs={"class": "thumbnail-form"}),
            "title": forms.Textarea(
                attrs={
                    "class": "title-form",
                    "rows": "2",
                    "onkeyup": "showTitleLength(value);",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "description-form",
                    "onkeyup": "showDescriptionLength(value);",
                }
            ),
        }