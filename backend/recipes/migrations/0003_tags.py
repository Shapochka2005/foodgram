from django.db import migrations

TAGS = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
    ('Десерт', 'dessert'),
    ('Напитки', 'drinks'),
)


def add_tags(apps, schema_editor):
    tag_model = apps.get_model('recipes', 'Tag')
    for name, slug in TAGS:
        tag_model.objects.get_or_create(
            slug=slug,
            defaults={'name': name},
        )


def remove_tags(apps, schema_editor):
    tag_model = apps.get_model('recipes', 'Tag')
    tag_model.objects.filter(
        slug__in=[slug for _, slug in TAGS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_tags, remove_tags),
    ]
