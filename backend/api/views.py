from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination

from api.filters import RecipeFilter
from users.models import User
from recipes.models import (
    Tag, Recipe, Ingredient, IngredientAmount
)
from .serializers import (
    UserSerializer, RoleSerializer, RegistrationSerializer,
    TokenSerializer, TagSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, RecipeToShoppingCart, RecipeToFavoriteList,
    IngredientSerializer, SubscriptionSerializer, UserSubscribeSerializer
)
from .permissions import (
    AdminModeratorAuthorPermission, IsAdminOrReadOnly,
    AdminOnly, AuthorPermission
)


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.username) + six.text_type(timestamp)
        )


account_activation_token = AccountActivationTokenGenerator()


@api_view(['POST'])
def registration(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user, created = User.objects.get_or_create(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
        )
        request.data.update({'id': user.id})
    except IntegrityError:
        raise ValidationError(
            'Некорректные username или email.'
        )
    return Response(request.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, 
        email=serializer.validated_data.get('email'),
        # password=serializer.validated_data.get('password')
    )    
    refresh = RefreshToken.for_user(user)
    token = {
        'auth_token': str(refresh.access_token),
    }
    return Response(token)


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [AdminOnly]
    lookup_field = 'pk'
    pagination_class = LimitOffsetPagination
    search_fields = ('^username',)

    @action(
        detail=False,
        methods=['get', 'patch', 'put', 'post'],
        url_name='me',
        permission_classes=[AuthorPermission],
        serializer_class=RoleSerializer
    )
    def me(self, request):
        serializer = self.serializer_class(request.user)
        if request.method == 'PATCH':
            serializer = self.serializer_class(
                request.user,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get', 'del', 'post'],
        url_name='subscriptions',
        serializer_class=SubscriptionSerializer        
    )
    def subscriptions(self, request):        
        queryset = User.objects.filter(
            subscription__in=[User.objects.get(id=request.user.id)]
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)  
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['delete', 'post'],
        url_name='subscribe',
    )
    def subscribe(self, request, pk):
        serializer = UserSubscribeSerializer(
            data={'pk': pk},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if 'deleted' in serializer.validated_data:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):   
    #filter_backends = (DjangoFilterBackend, )
    #filterset_class = RecipeFilter
    pagination_class = LimitOffsetPagination
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_destroy(self, recipe):
        self.request.user.favorite_recipes.remove(recipe)
        self.request.user.shoping_cart.recipes.remove(recipe)
        amounts = IngredientAmount.objects.filter(
            recipe=recipe
        ).delete()
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=True,
        methods=['delete', 'post'],
        url_name='shopping_cart'       
    )
    def shopping_cart(self, request, pk):
        serializer = RecipeToShoppingCart(
            data={'pk': pk},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if 'deleted' in serializer.validated_data:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete', 'post'],
        url_name='favorite'       
    )
    def favorite(self, request, pk):
        serializer = RecipeToFavoriteList(
            data={'pk': pk},
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if 'deleted' in serializer.validated_data:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)



class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
