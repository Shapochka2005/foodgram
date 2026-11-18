"""Компактное представление рецепта (избранное, подписки)."""
from rest_framework import serializers

from foodgram.utils import get_file_url

from .models import Recipe


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        return get_file_url(obj, 'image', self.context.get('request'))
