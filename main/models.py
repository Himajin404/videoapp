from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField("メールアドレス", unique=True)
    username = models.CharField("ユーザー名", max_length=50, default="ゲスト", unique=False)
    profile = models.TextField("プロフィール", max_length=500)
    icon = models.ImageField("アイコン", upload_to="icon/", blank=True)
    follow = models.ManyToManyField("User", related_name="followed", symmetrical=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name_plural = "ユーザー"

    def __str__(self):
        return f"{self.email}"
    
class AuthenticationCode(models.Model):
    code = models.CharField("認証コード", max_length=4)
    email = models.EmailField("メールアドレス", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    Uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "認証コード"

class Video(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField("タイトル", max_length=50)
    description = models.TextField("説明", max_length=500)
    thumbnail = models.ImageField("サムネイル", upload_to="thumbnail/")
    uploaded_at = models.DateTimeField("動画投稿時刻", auto_now_add=True)
    video = models.FileField("ビデオファイル", upload_to="uploaded_video/")
    views_count = models.IntegerField("視聴回数", default=0)

    class meta:
        verbose_name_plural = "ビデオ"

    def __str__(self):
        return self.title

