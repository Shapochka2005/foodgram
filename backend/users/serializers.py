from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from rest_framework import serializers

from foodgram.fields import Base64ImageField
from foodgram.utils import get_file_url
from recipes.minified import RecipeMinifiedSerializer
from recipes.models import Recipe

from .models import Subscription, User


class UserSerializer(serializers.ModelSerializer):
    """Публичное представление пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj,
        ).exists()

    def get_avatar(self, obj):
        return get_file_url(obj, 'avatar', self.context.get('request'))


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Регистрация пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class AvatarSerializer(serializers.ModelSerializer):
    """Загрузка аватара в base64."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('avatar',)

    def get_avatar(self, obj):
        return get_file_url(obj, 'avatar', self.context.get('request'))


class UserWithRecipesSerializer(UserSerializer):
    """Пользователь с рецептами — для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.query_params.get('recipes_limit') if request else None
        if limit and str(limit).isdigit():
            recipes = recipes[:int(limit)]
        serializer = RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


def get_recipe_queryset_for_subscriptions(user):
    """Рецепты пользователя, отсортированные по дате публикации."""
    return Recipe.objects.filter(author=user)
