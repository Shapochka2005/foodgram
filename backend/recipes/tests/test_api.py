import base64
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

User = get_user_model()

PASSWORD = 'StrongPass123'


def image_as_base64():
    buffer = BytesIO()
    Image.new('RGB', (30, 30), (30, 140, 90)).save(
        buffer,
        format='PNG',
    )
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{encoded}'


class RecipesApiTestCase(APITestCase):
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
        self.tag_lunch, _ = Tag.objects.get_or_create(
            slug='lunch',
            defaults={'name': 'Обед'},
        )
        self.tag_breakfast, _ = Tag.objects.get_or_create(
            slug='breakfast',
            defaults={'name': 'Завтрак'},
        )
        self.potato = Ingredient.objects.create(
            name='картофель',
            measurement_unit='г',
        )
        self.milk = Ingredient.objects.create(
            name='молоко',
            measurement_unit='мл',
        )
        self.recipe = self.create_recipe(self.author, 'Борщ')

    def create_recipe(self, author, name, tags=None, pub_date=None):
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            text='Описание рецепта',
            cooking_time=30,
            image='recipes/images/test.jpg',
            pub_date=pub_date or timezone.now(),
        )
        recipe.tags.set(tags or [self.tag_lunch])
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=self.potato,
            amount=100,
        )
        return recipe

    def authenticate(self, user=None):
        user = user or self.author
        response = self.client.post(
            '/api/auth/token/login/',
            {'email': user.email, 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {response.data["auth_token"]}'
        )

    def payload(self, **overrides):
        data = {
            'name': 'Новый рецепт',
            'text': 'Подробное описание',
            'cooking_time': 20,
            'tags': [self.tag_breakfast.id],
            'ingredients': [
                {'id': self.milk.id, 'amount': 200},
            ],
            'image': image_as_base64(),
        }
        data.update(overrides)
        return data


class RecipeReadTests(RecipesApiTestCase):
    def test_recipes_list_is_public(self):
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        recipe = response.data['results'][0]
        self.assertIn('tags', recipe)
        self.assertIn('author', recipe)
        self.assertIn('ingredients', recipe)
        self.assertFalse(recipe['is_favorited'])
        self.assertFalse(recipe['is_in_shopping_cart'])
        self.assertIn('/media/recipes/images/', recipe['image'])

    def test_recipe_detail_is_public(self):
        response = self.client.get(f'/api/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.recipe.id)
        self.assertEqual(
            response.data['ingredients'][0]['measurement_unit'],
            'г',
        )

    def test_recipe_detail_not_found(self):
        response = self.client.get('/api/recipes/9999/')
        self.assertEqual(response.status_code, 404)

    def test_recipes_are_sorted_by_publication_date(self):
        now = timezone.now()
        old = self.create_recipe(
            self.author,
            'Старый',
            pub_date=now - timedelta(days=2),
        )
        fresh = self.create_recipe(
            self.author,
            'Новый',
            pub_date=now,
        )
        response = self.client.get('/api/recipes/')
        ids = [item['id'] for item in response.data['results']]
        self.assertEqual(ids[0], fresh.id)
        self.assertEqual(ids[1], self.recipe.id)
        self.assertEqual(ids[2], old.id)

    def test_recipes_pagination(self):
        for index in range(7):
            self.create_recipe(self.author, f'Рецепт {index}')
        response = self.client.get('/api/recipes/?limit=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 8)
        self.assertIsNotNone(response.data['next'])

    def test_filter_by_tag(self):
        self.create_recipe(
            self.author,
            'Завтрак',
            tags=[self.tag_breakfast],
        )
        response = self.client.get('/api/recipes/?tags=lunch')
        names = [item['name'] for item in response.data['results']]
        self.assertEqual(names, ['Борщ'])

        response = self.client.get(
            '/api/recipes/?tags=lunch&tags=breakfast',
        )
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_author(self):
        response = self.client.get(
            f'/api/recipes/?author={self.reader.id}',
        )
        self.assertEqual(response.data['count'], 0)
        response = self.client.get(
            f'/api/recipes/?author={self.author.id}',
        )
        self.assertEqual(response.data['count'], 1)

    def test_filter_favorites_and_shopping_cart(self):
        Favorite.objects.create(user=self.reader, recipe=self.recipe)
        ShoppingCart.objects.create(user=self.reader, recipe=self.recipe)
        self.authenticate(self.reader)

        response = self.client.get('/api/recipes/?is_favorited=1')
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['is_favorited'])

        response = self.client.get('/api/recipes/?is_in_shopping_cart=1')
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(
            response.data['results'][0]['is_in_shopping_cart']
        )


class RecipeCreateTests(RecipesApiTestCase):
    def test_create_requires_auth(self):
        response = self.client.post(
            '/api/recipes/',
            self.payload(),
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_create_recipe(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(),
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Новый рецепт')
        self.assertEqual(response.data['author']['id'], self.author.id)
        self.assertEqual(response.data['tags'][0]['slug'], 'breakfast')
        self.assertEqual(
            response.data['ingredients'][0]['id'],
            self.milk.id,
        )
        self.assertEqual(response.data['ingredients'][0]['amount'], 200)
        self.assertIn('/media/recipes/images/', response.data['image'])
        self.assertEqual(Recipe.objects.count(), 2)

    def test_create_without_image(self):
        payload = self.payload()
        payload.pop('image')
        self.authenticate()
        response = self.client.post('/api/recipes/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)

    def test_create_with_empty_tags(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(tags=[]),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('tags', response.data)

    def test_create_with_duplicate_ingredients(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(
                ingredients=[
                    {'id': self.milk.id, 'amount': 100},
                    {'id': self.milk.id, 'amount': 200},
                ]
            ),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('ingredients', response.data)

    def test_create_with_empty_ingredients(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(ingredients=[]),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('ingredients', response.data)

    def test_create_with_empty_image(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(image=''),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('image', response.data)

    def test_create_with_zero_amount(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(
                ingredients=[{'id': self.milk.id, 'amount': 0}]
            ),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('ingredients', response.data)

    def test_create_with_unknown_tag(self):
        self.authenticate()
        response = self.client.post(
            '/api/recipes/',
            self.payload(tags=[9999]),
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class RecipeChangeTests(RecipesApiTestCase):
    def test_patch_by_author(self):
        self.authenticate()
        response = self.client.patch(
            f'/api/recipes/{self.recipe.id}/',
            {
                'name': 'Обновлённый борщ',
                'text': 'Новое описание',
                'cooking_time': 45,
                'tags': [self.tag_breakfast.id],
                'ingredients': [
                    {'id': self.milk.id, 'amount': 300},
                ],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Обновлённый борщ')
        self.assertEqual(response.data['tags'][0]['slug'], 'breakfast')
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.cooking_time, 45)
        self.assertEqual(
            self.recipe.recipe_ingredients.get().amount,
            300,
        )

    def test_patch_without_required_field(self):
        self.authenticate()
        response = self.client.patch(
            f'/api/recipes/{self.recipe.id}/',
            {'name': 'Без ингредиентов'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('ingredients', response.data)
        self.assertIn('tags', response.data)

    def test_patch_by_other_user_is_forbidden(self):
        self.authenticate(self.reader)
        response = self.client.patch(
            f'/api/recipes/{self.recipe.id}/',
            {'name': 'Чужое изменение'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_by_author(self):
        self.authenticate()
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/',
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Recipe.objects.filter(id=self.recipe.id).exists()
        )

    def test_delete_by_other_user_is_forbidden(self):
        self.authenticate(self.reader)
        response = self.client.delete(
            f'/api/recipes/{self.recipe.id}/',
        )
        self.assertEqual(response.status_code, 403)


class FavoriteAndCartTests(RecipesApiTestCase):
    def test_favorite_add_and_remove(self):
        self.authenticate(self.reader)
        url = f'/api/recipes/{self.recipe.id}/favorite/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['id'], self.recipe.id)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.reader,
                recipe=self.recipe,
            ).exists()
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

    def test_favorite_not_found(self):
        self.authenticate(self.reader)
        response = self.client.post('/api/recipes/9999/favorite/')
        self.assertEqual(response.status_code, 404)

    def test_shopping_cart_add_and_remove(self):
        self.authenticate(self.reader)
        url = f'/api/recipes/{self.recipe.id}/shopping_cart/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Борщ')

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

    def test_download_shopping_cart_sums_ingredients(self):
        second = self.create_recipe(self.author, 'Пюре')
        RecipeIngredient.objects.filter(recipe=second).delete()
        RecipeIngredient.objects.create(
            recipe=second,
            ingredient=self.potato,
            amount=250,
        )
        ShoppingCart.objects.create(user=self.reader, recipe=self.recipe)
        ShoppingCart.objects.create(user=self.reader, recipe=second)
        self.authenticate(self.reader)

        response = self.client.get(
            '/api/recipes/download_shopping_cart/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('картофель — 350 г', content)
        self.assertEqual(content.count('картофель'), 1)

    def test_download_shopping_cart_requires_auth(self):
        response = self.client.get(
            '/api/recipes/download_shopping_cart/',
        )
        self.assertEqual(response.status_code, 401)


class ShortLinkTests(RecipesApiTestCase):
    def test_get_link(self):
        response = self.client.get(
            f'/api/recipes/{self.recipe.id}/get-link/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['short-link'],
            f'http://testserver/s/{self.recipe.id}/',
        )

    def test_short_link_redirects_to_recipe(self):
        response = self.client.get(f'/s/{self.recipe.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            f'/recipes/{self.recipe.id}',
        )


class IngredientsAndTagsTests(RecipesApiTestCase):
    def test_ingredients_search_by_start(self):
        response = self.client.get('/api/ingredients/?name=карт')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'картофель')

    def test_ingredient_detail(self):
        response = self.client.get(
            f'/api/ingredients/{self.potato.id}/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['measurement_unit'], 'г')

    def test_tags_list_and_detail(self):
        response = self.client.get('/api/tags/')
        self.assertEqual(response.status_code, 200)
        slugs = [tag['slug'] for tag in response.data]
        self.assertIn('lunch', slugs)
        self.assertIn('breakfast', slugs)

        response = self.client.get(f'/api/tags/{self.tag_lunch.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['slug'], 'lunch')
