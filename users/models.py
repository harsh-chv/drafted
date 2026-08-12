from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds role system and profile fields.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        AUTHOR = 'author', 'Author'
        READER = 'reader', 'Reader'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.READER,
        help_text='User role determines permissions.',
    )
    bio = models.TextField(max_length=500, blank=True, default='')
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='Profile picture',
    )
    website = models.URLField(max_length=200, blank=True, default='')
    date_of_birth = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_author(self):
        return self.role in (self.Role.AUTHOR, self.Role.ADMIN)

    @property
    def is_reader(self):
        return self.role == self.Role.READER

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.following.count()

    @property
    def post_count(self):
        return self.posts.count()


class EmailOTP(models.Model):
    """
    Stores OTP codes sent to user emails during registration.
    OTP expires after 5 minutes.
    """
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'

    def __str__(self):
        return f'OTP for {self.email}'

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))

    @property
    def is_expired(self):
        """OTP expires after 5 minutes."""
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=5)
