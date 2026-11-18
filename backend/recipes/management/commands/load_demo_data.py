"""Наполнение базы демонстрационными пользователями и рецептами."""
import io
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)

DEMO_PASSWORD = 'Foodgram123'

DEMO_USERS = (
    {
        'username': 'anna',
        'email': 'anna@foodgram.ru',
        'first_name': 'Анна',
        'last_name': 'Петрова',
    },
    {
        'username': 'ivan',
        'email': 'ivan@foodgram.ru',
        'first_name': 'Иван',
        'last_name': 'Сидоров',
    },
    {
        'username': 'maria',
        'email': 'maria@foodgram.ru',
        'first_name': 'Мария',
        'last_name': 'Иванова',
    },
)

DEMO_RECIPES = (
    {
        'author': 'anna',
        'name': 'Куриный суп с картофелем',
        'text': (
            'Наваристый домашний суп: обжарьте куриное филе с луком и '
            'морковью, добавьте картофель, залейте водой и варите '
            '35 минут. Посолите в конце приготовления.'
        ),
        'cooking_time': 50,
        'tags': ('lunch',),
        'ingredients': (
            ('куриное филе', 300),
            ('картофель', 400),
            ('морковь', 100),
            ('лук репчатый', 80),
            ('соль', 5),
        ),
        'colors': ((246, 196, 83), (176, 96, 32)),
    },
    {
        'author': 'anna',
        'name': 'Паста с томатами и сыром',
        'text': (
            'Отварите макароны до состояния аль денте. Помидоры потушите '
            'с чесноком, соедините с пастой, посыпьте тёртым сыром.'
        ),
        'cooking_time': 25,
        'tags': ('lunch', 'dinner'),
        'ingredients': (
            ('макароны', 300),
            ('помидоры', 200),
            ('сыр', 100),
            ('чеснок', 10),
            ('соль', 4),
        ),
        'colors': ((233, 84, 62), (110, 22, 30)),
    },
    {
        'author': 'ivan',
        'name': 'Блины на молоке',
        'text': (
            'Смешайте муку, молоко, сахар и соль до однородности. '
            'Жарьте тонкие блины на разогретой сковороде по 2 минуты '
            'с каждой стороны.'
        ),
        'cooking_time': 30,
        'tags': ('breakfast', 'dessert'),
        'ingredients': (
            ('мука', 200),
            ('молоко', 300),
            ('сахар', 20),
            ('соль', 3),
            ('сливочное масло', 30),
        ),
        'colors': ((250, 214, 137), (191, 128, 53)),
    },
    {
        'author': 'ivan',
        'name': 'Сливочный рис с овощами',
        'text': (
            'Промойте рис и отварите до готовности. Морковь и лук '
            'обжарьте на сливочном масле, смешайте с рисом и прогрейте '
            'под крышкой 5 минут.'
        ),
        'cooking_time': 35,
        'tags': ('dinner',),
        'ingredients': (
            ('рис', 200),
            ('морковь', 100),
            ('лук репчатый', 80),
            ('сливочное масло', 30),
            ('соль', 4),
        ),
        'colors': ((197, 210, 148), (91, 112, 54)),
    },
    {
        'author': 'maria',
        'name': 'Говядина с картофелем',
        'text': (
            'Говядину нарежьте кусочками и обжарьте до корочки. '
            'Добавьте картофель и лук, влейте немного воды и тушите '
            'под крышкой 60 минут. Подавайте со сметаной.'
        ),
        'cooking_time': 90,
        'tags': ('lunch', 'dinner'),
        'ingredients': (
            ('говядина', 400),
            ('картофель', 500),
            ('лук репчатый', 100),
            ('сметана', 100),
            ('соль', 5),
        ),
        'colors': ((150, 97, 66), (63, 39, 27)),
    },
    {
        'author': 'maria',
        'name': 'Простой кекс к чаю',
        'text': (
            'Смешайте муку и сахар, добавьте молоко и растопленное '
            'сливочное масло. Выпекайте в форме 40 минут при 180 °C.'
        ),
        'cooking_time': 55,
        'tags': ('dessert',),
        'ingredients': (
            ('мука', 250),
            ('сахар', 150),
            ('молоко', 150),
            ('сливочное масло', 100),
        ),
        'colors': ((222, 176, 124), (129, 84, 45)),
    },
    {
        'author': 'maria',
        'name': 'Творожная запеканка',
        'text': (
            'Соедините творог, молоко, сахар и муку. Выложите массу '
            'в форму и запекайте 35 минут при 180 °C до золотистой '
            'корочки.'
        ),
        'cooking_time': 45,
        'tags': ('breakfast', 'dessert'),
        'ingredients': (
            ('творог', 400),
            ('молоко', 100),
            ('сахар', 60),
            ('мука', 50),
        ),
        'colors': ((248, 231, 197), (188, 151, 96)),
    },
    {
        'author': 'anna',
        'name': 'Домашний лимонад с мятой',
        'text': (
            'Разведите сахар в воде, добавьте сок лимона и листья '
            'мяты. Остудите напиток в холодильнике и подавайте '
            'с кубиками льда.'
        ),
        'cooking_time': 15,
        'tags': ('drinks',),
        'ingredients': (
            ('вода', 1000),
            ('сахар', 80),
            ('лимоны', 100),
            ('мята', 10),
        ),
        'colors': ((182, 226, 168), (52, 120, 74)),
    },
)


class Command(BaseCommand):
    """Создаёт тестовых пользователей, рецепты и избранное."""

    help = 'Наполняет базу демонстрационными данными.'

    @staticmethod
    def make_image(palette, name):
        width, height = 900, 600
        top, bottom = palette
        image = Image.new('RGB', (width, height), top)
        draw = ImageDraw.Draw(image)
        for y in range(height):
            ratio = y / (height - 1)
            color = tuple(
                int(top[channel] * (1 - ratio) + bottom[channel] * ratio)
                for channel in range(3)
            )
            draw.line(((0, y), (width, y)), fill=color)

        random.seed(name)
        for _ in range(18):
            radius = random.randint(35, 95)
            x = random.randint(0, width)
            y = random.randint(0, height)
            tint = tuple(
                min(255, channel + random.randint(20, 70))
                for channel in top
            )
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=tint,
            )

        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=88)
        return ContentFile(buffer.getvalue(), name=f'{name}.jpg')

    def handle(self, *args, **options):
        user_model = get_user_model()
        users = {}
        for data in DEMO_USERS:
            user, created = user_model.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users[data['username']] = user

        created_recipes = 0
        for index, data in enumerate(DEMO_RECIPES):
            author = users[data['author']]
            if Recipe.objects.filter(
                author=author,
                name=data['name'],
            ).exists():
                continue

            recipe = Recipe.objects.create(
                author=author,
                name=data['name'],
                text=data['text'],
                cooking_time=data['cooking_time'],
                image=self.make_image(
                    data['colors'],
                    f'recipe-{data["author"]}-{index}',
                ),
                pub_date=timezone.now() - timedelta(days=index),
            )
            recipe.tags.set(
                Tag.objects.filter(slug__in=data['tags'])
            )

            ingredient_names = [
                name for name, _ in data['ingredients']
            ]
            found = {
                ingredient.name: ingredient
                for ingredient in Ingredient.objects.filter(
                    name__in=ingredient_names,
                )
            }
            recipe_ingredients = []
            for name, amount in data['ingredients']:
                ingredient = found.get(name)
                if ingredient is None:
                    self.stderr.write(
                        f'Ингредиент «{name}» не найден, пропускаю.'
                    )
                    continue
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=amount,
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)
            created_recipes += 1

        recipes = list(Recipe.objects.order_by('id'))
        if len(recipes) >= 2:
            first, second = recipes[0], recipes[1]
            Favorite.objects.get_or_create(
                user=users['ivan'],
                recipe=first,
            )
            Favorite.objects.get_or_create(
                user=users['maria'],
                recipe=first,
            )
            Favorite.objects.get_or_create(
                user=users['anna'],
                recipe=second,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Демо-данные готовы: пользователей '
                f'{user_model.objects.count()}, рецептов '
                f'{Recipe.objects.count()}, добавлено сейчас '
                f'{created_recipes}.'
            )
        )
