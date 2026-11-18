from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from foodgram.pagination import LimitPageNumberPagination

from .models import Subscription, User
from .serializers import (
    AvatarSerializer,
    UserAvatarResponseSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserDetailView(generics.RetrieveAPIView):
    """Публичная страница пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class SubscriptionListView(generics.ListAPIView):
    """Список авторов, на которых подписан текущий пользователь."""

    serializer_class = UserWithRecipesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return User.objects.filter(
            subscribers__user=self.request.user,
        ).order_by('id')


class SubscribeView(APIView):
    """Подписка на автора и отписка от него."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Subscription.objects.filter(
            user=request.user,
            author=author,
        ).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Subscription.objects.create(user=request.user, author=author)
        serializer = UserWithRecipesSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(
            user=request.user,
            author=author,
        )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    """Добавление и удаление аватара текущего пользователя."""

    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        if request.user.avatar:
            request.user.avatar.delete(save=False)
        serializer.save()
        return Response(
            UserAvatarResponseSerializer(
                request.user,
                context={'request': request},
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
