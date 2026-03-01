# accounts/models.py

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ("director", "Director"),
        ("colonel_gs", "Colonel_GS"),
        ("gso_1", "GSO-1"),
        ("gso_2", "GSO-2"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"          # ← very useful: user.profile
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="student"               # ← optional: good default
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # You can add more fields later, e.g.:
    # phone = models.CharField(max_length=15, blank=True)
    # bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"

    @property
    def is_admin(self):
        return self.user_type == "admin"

    @property
    def is_student(self):
        return self.user_type == "student"

    @property
    def is_teacher(self):
        return self.user_type == "teacher"