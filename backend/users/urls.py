from django.urls import path

from .views import (
    AvatarView,
    SubscribeView,
    SubscriptionListView,
    UserDetailView,
)

urlpatterns = [
    path(
        'users/subscriptions/',
        SubscriptionListView.as_view(),
        name='subscriptions',
    ),
    path(
        'users/<int:pk>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe',
    ),
    path(
        'users/me/avatar/',
        AvatarView.as_view(),
        name='avatar',
    ),
    path(
        'users/<int:pk>/',
        UserDetailView.as_view(),
        name='user-detail',
    ),
]
