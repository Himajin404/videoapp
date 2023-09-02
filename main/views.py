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

from .forms import (
    EmailForm,
    RegistrationCodeForm,
)
from .models import AuthenticationCode

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

class TempRegistrationDoneView(TemplateView):
    template_name = "main/temp_registration_done.html"

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
        context["email"] = self.email
        return context

    def get_success_url(self):
        return reverse("signup", kwargs={"token": self.token})

class SignUpView(TemplateView):
    template_name = "main/signup.html"
