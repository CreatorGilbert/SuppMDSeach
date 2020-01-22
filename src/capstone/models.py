from django.db import models
from django.contrib.auth.models import User as big_user


class User(models.Model):
    user = models.ForeignKey(big_user, on_delete=models.CASCADE, unique=True)
    history = models.TextField()
