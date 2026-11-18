from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    IngredientDetailView,
    IngredientListView,
    RecipeViewSet,
    ShoppingCartDownloadView,
    TagDetailView,
    TagListView,
)

router = SimpleRouter()
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartDownloadView.as_view(),
        name='download-shopping-cart',
    ),
    path('ingredients/', IngredientListView.as_view(), name='ingredients'),
    path(
        'ingredients/<int:pk>/',
        IngredientDetailView.as_view(),
        name='ingredient-detail',
    ),
    path('tags/', TagListView.as_view(), name='tags'),
    path(
        'tags/<int:pk>/',
        TagDetailView.as_view(),
        name='tag-detail',
    ),
    path('', include(router.urls)),
]
