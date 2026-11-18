from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorites_count',
        'pub_date',
    )
    list_filter = ('tags', 'author')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('favorites_count', 'pub_date')
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)
    autocomplete_fields = ('author',)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        if obj is None:
            return 0
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created',)
