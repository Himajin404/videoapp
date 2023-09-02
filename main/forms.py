from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import AuthenticationCode

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

class RegistrationForm(forms.ModelForm):
    def __init__(self,email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email

    def clean_code(self):
        input_code = self.cleaned_data["code"]
        authentication_code_obj = get_object_or_404(
            AuthenticationCode, email=self.email
        )
        authentication_code = authentication_code_obj.code
        elapased_time = timezone.now() - authentication_code_obj.updated_at
        if elapased_time.seconds > 60:
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