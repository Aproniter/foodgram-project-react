import re

from hashlib import sha256

from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import models

from users.models import User
from recipes.models import (
    Tag, Recipe, Ingredient, IngredientAmount,
    ShopingCart
)


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=254
    )
    username = serializers.CharField(
        max_length=150
    )
    password = serializers.CharField(
        max_length=150
    )
    first_name = serializers.CharField(
        max_length=150
    )
    last_name = serializers.CharField(
        max_length=150
    )

    class Meta:
        fields = ('email', 'username', 'password')

    def validate_username(self, data):
        if re.match(r'^[\\w.@+-]+\\z', data):
            raise serializers.ValidationError(
                'Недопустимые символы в username.'
            )
        if data == 'me':
            raise serializers.ValidationError(
                'Использовать имя "me" в качестве username запрещено.'
            )
        return data


class TokenSerializer(serializers.Serializer):
    email = serializers.CharField(
        max_length=150
    )
    password = serializers.CharField(
        max_length=150
    )

    class Meta:
        fields = ('token', 'email', 'password')


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed'
        )
        model = User

    def get_is_subscribed(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        return (obj in
        self.context['request'].user.subscriptions.all())


class UserSubscribeSerializer(UserSerializer):
    recipes_limit = serializers.IntegerField()

    def validate(self, data):
        user = self.context['request'].user
        subscribe = get_object_or_404(
            User, 
            pk=self.initial_data['pk']
        )
        subscriptions = user.subscriptions.filter(
            pk=subscribe.pk
        ).exists()
        if self.context['request'].method == 'DELETE':
            if subscriptions:
                user.subscriptions.remove(subscribe)
                return {'deleted': True}
            else:
                raise serializers.ValidationError(
                    {'errors': 'Вы не подписаны на этого пользователя.'}
                )
        if not subscriptions:
            if subscribe != user:
                user.subscriptions.add(subscribe)
            else:
                raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на себя.'}
                )
        else:
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя.'}
            )
        recipes_subscribe = Recipe.objects.filter(
                author=subscribe
        )[:self.context['request'].data['recipes_limit']]
        recipes = RecipeReadSerializer(
            recipes_subscribe,
            many=True,
            context=self.context
        )
        return {
                "email": subscribe.email,
                "id": subscribe.id,
                "username": subscribe.username,
                "first_name": subscribe.first_name,
                "last_name": subscribe.last_name,
                "is_subscribed": True,
                "recipes": recipes.data,
                "recipes_count": recipes_subscribe.count()
        }


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = User

    def validate(self, data):
        if not self.context['request'].user.is_staff:
            data['role'] = self.context['request'].user.role
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user
        if 'current_password' not in data:
            raise serializers.ValidationError(
                    {'current_password': 'Обязательное поле.'}
                )
        if 'new_password' not in data:
            raise serializers.ValidationError(
                    {'new_password': 'Обязательное поле.'}
                )            
        if not check_password(data['current_password'], user.password):
            raise serializers.ValidationError(
                    {'current_password': 'Неверный пароль.'}
                )
        return data

class Recipes(serializers.Field):

    def to_representation(self, value):
        return [
            {
                'id': i.id,
                'name': i.name,
                'image': i.image,
                'cooking_time': i.cooking_time
            } for i in value.recipes.all()
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(source='subscriptions')
    recipes = Recipes(source='*')
    recipes_count = serializers.IntegerField(
        source='recipes.count'
    )

    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        model = User


class TagSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = (
            "id",
            "name",
            "color",
            "slug"
        )
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'    
        model = Ingredient


class IngredientField(serializers.RelatedField):
    amount = {}
    def to_representation(self, data):
        return {
                'id': data.id,
                'name': data.name,
                'measurement_unit': data.measurement_unit,
                'amount': self.amount[data.id]
        }

    def to_internal_value(self, data):
        ingredient_amount = {
            'amount': data['amount'],
            'ingredient': Ingredient.objects.get(id=data['id'])
        }
        self.amount.update({data['id']: data['amount']})
        return ingredient_amount


class IngredientReadField(serializers.Field):

    def to_representation(self, data):
        return [{
                'id': i.id,
                'name': i.name,
                'measurement_unit': i.measurement_unit,
                'amount': IngredientAmount.objects.get(
                    recipe=data.id,
                    ingredient=i.id
                ).amount
        } for i in data.ingredients.all()]


class TagField(serializers.RelatedField):
    def to_representation(self, data):
        return {
                'id': data.id,
                'name': data.name,
                'color': data.color,
                'slug': data.slug
        }

    def to_internal_value(self, data):
        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagField(
        many=True,
        queryset=Tag.objects.all()
    )
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    
    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        favorite = (
            obj in 
            self.context['request'].user.favorite_recipes.all()
            if self.context['request'].user.is_authenticated 
            else False 
        )
        return favorite

    def get_is_in_shopping_cart(self, obj):
        try:
            in_shopping_cart = (
                obj in 
                self.context['request'].user.shoping_cart.recipes.all()
                if self.context['request'].user.is_authenticated 
                else False 
            )
            return in_shopping_cart
        except AttributeError:
            return False


class RecipeWriteSerializer(RecipeSerializer):
    ingredients = IngredientField(
        many=True,
        queryset=Ingredient.objects.all(),
    )

    def _create_amount(self, obj, data):
        amounts = IngredientAmount.objects.filter(
            recipe=obj
        ).delete()
        amount_objs = [
            IngredientAmount(
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
                recipe=obj
            )
            for ingredient in data.get('ingredients')
        ]
        amounts = IngredientAmount.objects.bulk_create(amount_objs)
    
    def create(self, data):
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            cooking_time=self.validated_data.get('cooking_time'),
            text=self.validated_data.get('text'),
            name=self.validated_data.get('name'),
            image=self.validated_data.get('image'),
        )
        recipe.ingredients.set(
            [i['ingredient'] for i in self.validated_data.get('ingredients')]
        )
        recipe.tags.set(self.validated_data.get('tags'))
        self._create_amount(recipe, self.validated_data)
        return recipe

    def update(self, obj, data):
        obj.cooking_time = self.validated_data.get('cooking_time')
        obj.text = self.validated_data.get('text', obj.text)
        obj.name = self.validated_data.get('name', obj.name)
        obj.image = self.validated_data.get('image', obj.image)
        obj.ingredients.set(
            [i['ingredient'] for i in self.validated_data.get('ingredients')]
        )
        obj.tags.set(self.validated_data.get('tags'))
        self._create_amount(obj, self.validated_data)
        obj.save()
        return obj

    def get_is_favorited(self, obj):
        try:
            self.context['request'].user.favorite_recipes.add(obj)      
            return True
        except:
            return False

    def get_is_in_shopping_cart(self, obj):
        try:
            shoping_cart = ShopingCart.objects.get(
                user=self.context['request'].user
            )
        except ShopingCart.DoesNotExist:
            shoping_cart = ShopingCart.objects.create()
            shoping_cart.user.add(self.context['request'].user)
             
        shoping_cart.recipes.add(obj)
        return True


class RecipeReadSerializer(RecipeSerializer):
    ingredients = IngredientReadField(
        source='*'
    )


class RecipeToShoppingCart(serializers.Serializer):
    def validate(self, data):        
        recipe = get_object_or_404(
            Recipe, 
            pk=self.initial_data['pk']
        )
        try:
            shoping_cart = ShopingCart.objects.get(
                user=self.context['request'].user
            )
        except ShopingCart.DoesNotExist:
            shoping_cart = ShopingCart.objects.create()
            shoping_cart.user.add(self.context['request'].user)
            
        if self.context['request'].method == 'DELETE':
            if shoping_cart.recipes.filter(pk=recipe.pk).exists():
                shoping_cart.recipes.remove(recipe)
                return {'deleted': True}
            else:
                raise serializers.ValidationError(
                    {'errors': 'Рецепта нет в списке покупок.'}
                )
        if not shoping_cart.recipes.filter(pk=recipe.pk).exists():
            shoping_cart.recipes.add(recipe)
        else:
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже есть в списке покупок.'}
            )
        return {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image,
                'cooking_time': recipe.cooking_time,
        }


class RecipeToFavoriteList(serializers.Serializer):
    def validate(self, data):
        user = self.context['request'].user  
        recipe = get_object_or_404(
            Recipe, 
            pk=self.initial_data['pk']
        )        
        if self.context['request'].method == 'DELETE':
            if user.favorite_recipes.filter(pk=recipe.pk).exists():
                user.favorite_recipes.remove(recipe)
                return {'deleted': True}
            else:
                raise serializers.ValidationError(
                    {'errors': 'Рецепта нет в избранном.'}
                )
        if not user.favorite_recipes.filter(pk=recipe.pk).exists():
            user.favorite_recipes.add(recipe)
        else:
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже есть в избранном.'}
            )
        return {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image,
                'cooking_time': recipe.cooking_time,
        }
