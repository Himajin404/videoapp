from typing import Any, Dict
from django import http
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import TemplateView, FormView, ListView
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy, reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import (EmailForm, 
                    PasswordForm, 
                    RegistrationCodeForm, 
                    EmailAuthenticationForm, 
                    PasswordResetEmailForm, 
                    PasswordResetForm, 
                    VideoUploadForm, 
                    VideoSearchForm,)
from .models import AuthenticationCode, Video
from django.contrib.auth.views import LoginView


User = get_user_model()

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "main/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = Video.objects.all().order_by("-uploaded_at")
        context["videos"] = video
        return context

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
        "email": email,
        "token": token,
    }
    return render(request, "main/temp_registration_done.html", context)

class SignUpView(FormView):
    template_name = "main/signup.html"
    form_class = PasswordForm
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        self.token = self.kwargs["token"]
        try:
            self.email = signing.loads(self.token)
        except signing.BadSignature:
            return HttpResponseBadRequest("不正なURLです。")
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


class LoginView(LoginView):
    template_name = "main/login.html"
    form_class = EmailAuthenticationForm
    redirect_authenticated_user = True


def password_reset_send_email(email):
    random_code = generate_random_code(email)
    context = {
        "email": email,
        "random_code": random_code,
    }
    subject = "パスワード再設定について"
    message = render_to_string("mail_text/password_reset.txt", context)
    from_email = None
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

class PasswordResetEmailView(TemplateView):
    template_name = "main/password_reset_email.html"
    form_class = PasswordResetEmailForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        self.token = signing.dumps(email)
        password_reset_send_email(email)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("password_reset_confirmation", kwargs={"token": self.token})

class PasswordResetConfirmationView(TemplateView):
    template_name = "main/password_reset_confirmation.html"
    form_class= RegistrationCodeForm

    def dispatch(self, request, *args, **kwargs):
        self.token = self.kwargs["token"]
        try:
            self.email = signing.loads(self.token)
        except signing.BadSignature:
            return HttpResponseBadRequest("不正なURLです。")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["email"] = self.email
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"] = self.token
        context["email"] = self.email
        return context

    def get_success_url(self):
        return reverse("password_reset", kwargs={"token": self.token})

class PasswordResetView(TemplateView):
    template_name = "main/password_reset.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        self.token = self.kwargs["token"]
        try:
            self.email = signing.loads(self.token)[0]
        except signing.BadSignature:
            return HttpResponseBadRequest("不正なURLです。")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        new_password = form.cleaned_data["new_password1"]
        new_password = make_password(new_password)
        user = User.objects.filter(email=self.email)
        user.update(password=new_password)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.email
        return context

@require_POST
def resend_password_reset_email(request, token):
    try:
        email = signing.loads(token)
    except signing.BadSignature:
        return HttpResponseBadRequest("不正なURLです。")
    form = RegistrationCodeForm
    password_reset_send_email(email)
    messages.success(request, "入力されたメールアドレスに送信しました。")
    context = {
        "form": form,
        "email": email,
        "token": token,
    }
    return render(request, "main/password_reset_confirmation.html", context)


class VideoUploadView(LoginRequiredMixin, FormView):
    template_name = "main/video_upload.html"
    form_class = VideoUploadForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        video = form.save(commit=False)
        video.user = self.request.user
        video.save()
        return super().form_valid(form)

class SearchVideoView(FormView):
    template_name = "main/video_search.html"
    model = Video
    context_object_name = "videos"

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-uploaded_at")
        if self.form.is_valid():
            keyword = self.form.cleaned_data["keyword"]
    