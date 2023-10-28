from typing import Any
from django import http
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView, FormView
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy, reverse
from django.contrib.auth.hashers import make_password

from .forms import (EmailForm, PasswordForm, RegistrationCodeForm, EmailAuthenticationForm)
from .models import AuthenticationCode
from django.contrib.auth.views import LoginView

User = get_user_model()

class HomeView(TemplateView):
    template_name = "main/home.html"

def generate_random_code(email):
    random_number = get_random_string(4, "0123456789")
    AuthenticationCode.objects.update_or_create(
        email=email, defaults={"code": random_number}
    )
    return random_number

def registration_send_email(email):
    random_code = generate_random_code(email)
    context = {
        "email": email,
        "random_code": random_code,
    }
    subject = "Video Appの本登録について"
    message = render_to_string("mail_text/registration.txt", context)
    from_email = None
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

class TempRegistrationView(FormView):
    template_name = "main/temp_registration.html"
    form_class = EmailForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        self.email = email
        self.token = signing.dumps(email)#トークン暗号化
        registration_send_email(email)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("temp_registration_done", kwargs={"token": self.token})   

class TempRegistrationDoneView(FormView):
    template_name = "main/temp_registration_done.html"
    form_class = RegistrationCodeForm

    def dispatch(self, request, *args, **kwargs):
        self.token = self.kwargs["token"]
        try:
            self.email = signing.loads(self.token)
        except signing.BadSignature:
            return HttpResponseBadRequest("不正なURLです。")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"] = self.token
        return context

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["email"] = self.email
        return kwargs

    def get_success_url(self):
        return reverse("signup", kwargs={"token": self.token})


@require_POST
def resend_registration_email(request, token):
    try:
        email = signing.loads(token)
    except signing.BadSignature:
        return HttpResponseBadRequest("不正なURLです。")
    form = RegistrationCodeForm
    registration_send_email(email)
    messages.success(request, "入力されたメールアドレスに送信しました。")
    context = {
        "form": form,
        "email":email,
        "token": token,
    }
    return render(request, "main/temp_registration_done.html", context)


class SignUpView(TemplateView):
    template_name = "main/signup.html"
    form_class = PasswordForm
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        self.token = self.kwargs["token"]
        try:
            self.email = signing.loads(self.token)
        except signing.BadSignature:
            return HttpResponseBadRequest("不正なURLです")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        password = form.cleaned_data["password"]
        password = make_password(password)
        User.objects.create(username="ゲスト", email=self.email, password=password)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.email
        return context


class LoginView(TemplateView):
    template_name = "main/login.html"
    form_class = EmailAuthenticationForm
    redirect_authticated_user = True