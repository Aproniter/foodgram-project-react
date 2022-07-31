from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

from recipes.models import Recipe


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLE = (
        (USER, 'User'),
        (MODERATOR, 'Moderator'),
        (ADMIN, 'Admin'),
    )
    username = models.CharField(
        max_length=255,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]*$',
            message='Имя пользователя содержит недопустимые символы',
            code='invalid_username'
        ),
        ]
    )
    first_name = models.CharField(
        max_length=150,
        blank=True
    )
    last_name = models.CharField(
        max_length=150,
        blank=True
    )
    password = models.CharField(
        max_length=150        
    )
    role = models.CharField(
        max_length=255,
        choices=ROLE,
        default=USER,
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    favorite_recipes = models.ManyToManyField(
        Recipe,
        related_name='users',
        blank=True,
    )
    subscriptions = models.ManyToManyField(
        'User',
        related_name='subscription',
        blank=True,
    )
    shoping_cart = models.ForeignKey(
        to='recipes.ShopingCart',
        on_delete=models.CASCADE,
        related_name='user',
        blank=True,
        null=True
    )

    @property
    def is_admin(self):
        return self.is_staff or self.role == self.ADMIN

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
