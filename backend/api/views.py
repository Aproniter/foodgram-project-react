from django.conf import settings
from django.http import FileResponse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django_filters import rest_framework as filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination

from users.models import User
from recipes.models import (
    Tag, Recipe, Ingredient, IngredientAmount, ShopingCart
)
from .serializers import (
    UserSerializer, RoleSerializer, RegistrationSerializer,
    TokenSerializer, TagSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, RecipeToShoppingCart, RecipeToFavoriteList,
    IngredientSerializer, SubscriptionSerializer, UserSubscribeSerializer,
    ChangePasswordSerializer
)
from .permissions import (
    AdminModeratorAuthorPermission, IsAdminOrReadOnly,
    AdminOnly, AuthorPermission, IsAuthenticatedOrReadOnly
)
from .services import get_file
from .filters import RecipeFilterBackend


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.username) + six.text_type(timestamp)
        )


account_activation_token = AccountActivationTokenGenerator()


@api_view(['POST'])
@permission_classes([AllowAny])
def registration(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user, created = User.objects.get_or_create(
            username=request.data['username'],
            email=request.data['email'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
        )
        user.set_password(request.data['password'])
        user.save()        
        request.data.update({'id': user.id})
    except IntegrityError:
        raise ValidationError(
            'Некорректные данные.'
        )
    return Response(request.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, 
        email=serializer.validated_data.get('email'),
    )
    if not check_password(
        serializer.validated_data.get('password'), user.password
    ):
        return Response(
            {'errors': 'Неверный пароль.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        token = Token.objects.create(user=user)
    resp = {
        'auth_token': token.key,
    }
    return Response(resp, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    try:
        Token.objects.get(user=request.user).delete()
    except Token.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)


class UsersViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AdminOnly]
    lookup_field = 'pk'
    pagination_class = LimitOffsetPagination
    search_fields = ('^username', '^email')

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
        permission_classes=[AuthorPermission],
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
        permission_classes=[AuthorPermission],
    )
    def subscribe(self, request, pk):
        serializer = UserSubscribeSerializer(
            data={'pk': pk},
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if 'deleted' in serializer.validated_data:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['post'],
        url_name='set_password',
        permission_classes=[AuthorPermission],
        serializer_class=ChangePasswordSerializer
    )
    def set_password(self, request):
        serializer = self.serializer_class(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
        if serializer.is_valid(raise_exception=True):
            request.user.set_password(
                serializer.validated_data.get('new_password')
            )
            request.user.save()
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RecipeViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination
    search_fields = ('^author', '^tags', '^name')
    queryset = Recipe.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('tags',)
    filterset_class  = RecipeFilterBackend

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
        url_name='shopping_cart',
        permission_classes=[IsAuthenticated]
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
        url_name='favorite',
        permission_classes=[IsAuthenticated]
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


    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        if hasattr(request.user, 'shoping_cart'):
            shoping_cart = request.user.shoping_cart
        else:
            return Response(status=status.HTTP_404_BAD_REQUEST)        
        send_file = get_file(shoping_cart)
        response = FileResponse(send_file, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping-list.txt"'
        return response


class IngredientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ('^name',)
    
    def get_queryset(self):
        queryset = (
            Ingredient.objects.filter(
                name__istartswith=self.request.query_params.get(
                    'name'
                ).decode('utf-8')
            ) 
            if self.request.query_params.get('name') 
            else Ingredient.objects.all()
        )
        return queryset
