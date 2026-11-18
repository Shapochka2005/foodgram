from django_filters import rest_framework as filters

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    @staticmethod
    def _is_true(value):
        return str(value) == '1'

    def filter_tags(self, queryset, name, value):
        request = self.request
        slugs = []
        if request is not None:
            slugs = request.query_params.getlist('tags')
        if not slugs and value:
            slugs = value.split(',')
        slugs = [slug for slug in slugs if slug]
        if not slugs:
            return queryset
        return queryset.filter(tags__slug__in=slugs).distinct()

    def filter_is_favorited(self, queryset, name, value):
        if not self._is_true(value):
            return queryset
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(
            favorites__user=self.request.user,
        ).distinct()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self._is_true(value):
            return queryset
        if not self.request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(
            shopping_cart__user=self.request.user,
        ).distinct()
