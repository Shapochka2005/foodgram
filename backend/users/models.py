from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


login_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Введите корректный юзернейм: разрешены только буквы, '
            'цифры и символы @/./+/-/_.',
)


class User(AbstractUser):
    """Пользователь Foodgram. Вход выполняется по email."""

    email = models.EmailField('Адрес электронной почты', unique=True)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        null=True,
        blank=True,
    )
    username = models.CharField(
        'Юзернейм',
        max_length=150,
        unique=True,
        validators=[login_validator],
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )
    created = models.DateTimeField('Дата подписки', auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-created',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.author}'
