import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из data/ingredients.csv."""

    help = 'Загружает ингредиенты из CSV-файла проекта.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=None,
            help='Путь к CSV-файлу с ингредиентами.',
        )

    @staticmethod
    def find_csv():
        candidates = (
            Path(settings.BASE_DIR) / 'data' / 'ingredients.csv',
            Path(settings.BASE_DIR).parent / 'data' / 'ingredients.csv',
            Path('/app/data/ingredients.csv'),
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def handle(self, *args, **options):
        path = Path(options['path']) if options['path'] else self.find_csv()
        if path is None or not path.exists():
            self.stderr.write(
                self.style.ERROR(
                    'Файл ingredients.csv не найден. '
                    'Укажите путь через --path.'
                )
            )
            return

        self.stdout.write(f'Читаю ингредиенты из {path}')
        ingredients = []
        seen = set()
        with path.open(encoding='utf-8', newline='') as csv_file:
            for row in csv.reader(csv_file):
                if len(row) < 2:
                    continue
                name = row[0].strip()
                unit = row[1].strip()
                if not name or not unit:
                    continue
                key = (name, unit)
                if key in seen:
                    continue
                seen.add(key)
                ingredients.append(
                    Ingredient(name=name, measurement_unit=unit)
                )

        Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
            batch_size=500,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Ингредиентов в базе: {Ingredient.objects.count()}'
            )
        )
