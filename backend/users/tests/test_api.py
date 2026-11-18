import base64
from io import BytesIO

from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Recipe

User = get_user_model()

PASSWORD = 'StrongPass123'
NEW_PASSWORD = 'Vx9#Lm2Qw7'


def image_as_base64():
    buffer = BytesIO()
    Image.new('RGB', (20, 20), (200, 100, 50)).save(
        buffer,
        format='PNG',
    )
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{encoded}'


class UsersApiTestCase(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password=PASSWORD,
            first_name='Иван',
            last_name='Петров',
        )
        self.reader = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password=PASSWORD,
            first_name='Пётр',
            last_name='Сидоров',
        )

    def authenticate(self, user=None):
        user = user or self.author
        response = self.client.post(
            '/api/auth/token/login/',
            {'email': user.email, 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['auth_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        return token


class RegistrationTests(UsersApiTestCase):
    def test_register_user(self):
        response = self.client.post(
            '/api/users/',
            {
                'email': 'new@example.com',
                'username': 'new_user',
                'password': NEW_PASSWORD,
                'first_name': 'Новый',
                'last_name': 'Пользователь',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertNotIn('password', response.data)
        user = User.objects.get(email='new@example.com')
        self.assertTrue(user.check_password(NEW_PASSWORD))

    def test_register_with_duplicate_email(self):
        response = self.client.post(
            '/api/users/',
            {
                'email': self.author.email,
                'username': 'another',
                'password': NEW_PASSWORD,
                'first_name': 'Ещё',
                'last_name': 'Один',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            '/api/auth/token/login/',
            {'email': self.author.email, 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.status_code, 400)

    def test_register_without_first_name(self):
        response = self.client.post(
            '/api/users/',
            {
                'email': 'no-name@example.com',
                'username': 'no_name',
                'password': NEW_PASSWORD,
                'last_name': 'Пользователь',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('first_name', response.data)

    def test_register_without_last_name(self):
        response = self.client.post(
            '/api/users/',
            {
                'email': 'no-last@example.com',
                'username': 'no_last',
                'password': NEW_PASSWORD,
                'first_name': 'Новый',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('last_name', response.data)

    def test_login_returns_auth_token(self):
        response = self.client.post(
            '/api/auth/token/login/',
            {'email': self.author.email, 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.data)


class ProfileTests(UsersApiTestCase):
    def test_me_requires_auth(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, 401)

    def test_me_returns_current_user(self):
        self.authenticate()
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'author')
        self.assertIsNone(response.data['avatar'])

    def test_user_detail_is_public(self):
        response = self.client.get(f'/api/users/{self.author.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['is_subscribed'])

    def test_users_list_supports_pagination(self):
        for index in range(5):
            User.objects.create_user(
                username=f'user{index}',
                email=f'user{index}@example.com',
                password=PASSWORD,
            )
        response = self.client.get('/api/users/?limit=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 7)
        self.assertIsNotNone(response.data['next'])

    def test_avatar_upload_and_delete(self):
        self.authenticate()
        response = self.client.put(
            '/api/users/me/avatar/',
            {'avatar': image_as_base64()},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('/media/users/avatars/', response.data['avatar'])

        self.author.refresh_from_db()
        self.assertTrue(self.author.avatar)

        response = self.client.delete('/api/users/me/avatar/')
        self.assertEqual(response.status_code, 204)
        self.author.refresh_from_db()
        self.assertFalse(self.author.avatar)

    def test_change_password(self):
        self.authenticate()
        response = self.client.post(
            '/api/users/set_password/',
            {
                'current_password': PASSWORD,
                'new_password': 'NewStrongPass456',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 204)
        self.author.refresh_from_db()
        self.assertTrue(self.author.check_password('NewStrongPass456'))


class SubscriptionTests(UsersApiTestCase):
    def test_subscribe_to_author(self):
        self.authenticate(self.reader)
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_subscribed'])

        response = self.client.get('/api/users/subscriptions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.author.id)

    def test_subscribe_to_self_is_forbidden(self):
        self.authenticate(self.author)
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, 400)

    def test_double_subscription_is_forbidden(self):
        self.authenticate(self.reader)
        self.client.post(f'/api/users/{self.author.id}/subscribe/')
        response = self.client.post(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, 400)

    def test_unsubscribe(self):
        self.authenticate(self.reader)
        self.client.post(f'/api/users/{self.author.id}/subscribe/')
        response = self.client.delete(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, 204)
        response = self.client.delete(
            f'/api/users/{self.author.id}/subscribe/',
        )
        self.assertEqual(response.status_code, 400)

    def test_subscriptions_return_limited_recipes(self):
        for index in range(4):
            Recipe.objects.create(
                author=self.author,
                name=f'Рецепт {index}',
                text='Описание',
                cooking_time=10,
                image='recipes/images/test.jpg',
            )
        self.authenticate(self.reader)
        self.client.post(f'/api/users/{self.author.id}/subscribe/')

        response = self.client.get(
            '/api/users/subscriptions/?recipes_limit=2',
        )
        self.assertEqual(response.status_code, 200)
        result = response.data['results'][0]
        self.assertEqual(result['recipes_count'], 4)
        self.assertEqual(len(result['recipes']), 2)

    def test_is_subscribed_flag(self):
        self.authenticate(self.reader)
        self.client.post(f'/api/users/{self.author.id}/subscribe/')
        response = self.client.get(f'/api/users/{self.author.id}/')
        self.assertTrue(response.data['is_subscribed'])
