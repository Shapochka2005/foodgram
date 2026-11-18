"""
URL configuration for the Foodgram project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Короткие ссылки вида /s/<id>/ ведут на страницу рецепта.
    path(
        's/<int:pk>/',
        RedirectView.as_view(url='/recipes/%(pk)s', permanent=False),
        name='short-link',
    ),
    # Явные маршруты подписок объявляем до djoser, чтобы
    # users/subscriptions/ не был перехвачен как users/<id>/.
    path('api/', include('users.urls')),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include('recipes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

admin.site.site_header = 'Администрирование Foodgram'
admin.site.site_title = 'Foodgram'
admin.site.index_title = 'Управление проектом'
