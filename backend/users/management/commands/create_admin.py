import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создаёт администратора из переменных окружения."""

    help = 'Создаёт или обновляет суперпользователя Foodgram.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        email = os.getenv('ADMIN_EMAIL', 'admin@foodgram.ru')
        password = os.getenv('ADMIN_PASSWORD', 'FoodgramAdmin123')
        username = os.getenv('ADMIN_USERNAME', 'admin')
        first_name = os.getenv('ADMIN_FIRST_NAME', 'Администратор')
        last_name = os.getenv('ADMIN_LAST_NAME', 'Foodgram')

        user, created = user_model.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not created:
            user.username = user.username or username
            user.is_staff = True
            user.is_superuser = True

        user.set_password(password)
        user.save()

        action = 'создан' if created else 'обновлён'
        self.stdout.write(
            self.style.SUCCESS(
                f'Администратор {email} {action}.'
            )
        )
