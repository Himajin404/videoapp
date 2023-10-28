from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import AuthenticationCode
from django.contrib.auth import get_user_model, authenticate


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
        print(3)
        authentication_code = authentication_code_obj.code
        elapased_time = timezone.now() - authentication_code_obj.updated_at
        if elapased_time.seconds > 30:
            raise ValidationError("この認証コードは無効です。新しい認証コードを発行してください。")
        print(2)
        if input_code != authentication_code:
            raise ValidationError("認証コードが正しくありません。")
        print(1)
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