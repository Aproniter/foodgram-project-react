import re

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import models

from users.models import User
from recipes.models import Tag, Recipe, Ingredient, IngredientAmount


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
        max_length=255
    )
    password = serializers.CharField(
        max_length=255
    )

    class Meta:
        fields = ('token', 'email', 'password')

    # def validate_username(self, data):
    #     if re.match(r'^[\\w.@+-]+\\z', data):
    #         raise serializers.ValidationError(
    #             'Недопустимые символы в username.'
    #         )
    #     if data == 'me':
    #         raise serializers.ValidationError(
    #             'Использовать имя "me" в качестве username запрещено.'
    #         )
    #     return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = User


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = User

    def validate(self, data):
        if not self.context['request'].user.is_staff:
            data['role'] = self.context['request'].user.role
        return data


class Recipes(serializers.Field):

    def to_representation(self, value):
        ret = [
            {
                'id': i.id,
                'name': i.name,
                'image': i.image,
                'cooking_time': i.cooking_time
            } for i in value.recipes.all()
        ]
        return ret


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
        ret = {
                'id': data.id,
                'name': data.name,
                'measurement_unit': data.measurement_unit,
                'amount': self.amount[data.id]
        } 
        return ret

    def to_internal_value(self, data):
        amount = IngredientAmount.objects.create(
            ingredient=Ingredient.objects.get(id=data['id']),
            amount=data['amount']
        )
        ingredient_amount = {
            'amount_id': amount.id,
            'ingredient': Ingredient.objects.get(id=data['id'])
        }
        self.amount.update({data['id']: data['amount']})
        return ingredient_amount


class IngredientReadField(serializers.Field):

    def to_representation(self, data):
        ret = [{
                'id': i.id,
                'name': i.name,
                'measurement_unit': i.measurement_unit,
                'amount': IngredientAmount.objects.get(
                    recipe=data.id,
                    ingredient=i.id
                ).amount
        } for i in data.ingredients.all()]
        return ret


class TagField(serializers.RelatedField):
    def to_representation(self, data):
        ret = {
                'id': data.id,
                'name': data.name,
                'color': data.color,
                'slug': data.slug
        } 
        return ret

    def to_internal_value(self, data):
        return data


class AuthorField(serializers.Field):
    def to_representation(self, data):
        ret = {
                'id': data.author.id,
                'email': data.author.email,
                'username': data.author.username,
                'first_name': data.author.first_name,
                'last_name': data.author.last_name,
                'is_subscribed': (
                    data.author in 
                    self.context['request'].user.subscriptions.all()
                )
        } 
        return ret

    def to_internal_value(self, data):
        return data


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientField(
        many=True,
        queryset=Ingredient.objects.all(),
    )
    tags = TagField(
        many=True,
        queryset=Tag.objects.all()
    )
    author = AuthorField(
        required=False,
    )    
    
    class Meta:
        fields = '__all__'
        model = Recipe
    
    def create(self, data):
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            cooking_time=data.get('cooking_time'),
            text=data.get('text'),
            name=data.get('name'),
            image=data.get('image'),
        )        
        recipe.ingredients.set([i['ingredient'] for i in data.get('ingredients')])
        recipe.tags.set(data.get('tags'))
        amounts = IngredientAmount.objects.filter(
            id__in=[i['amount_id'] for i in data.get('ingredients')]
        )
        
        for amount in amounts:
            amount.recipe=recipe
            amount.save()
        self.context['request'].user.favorite_recipes.add(recipe)
        return recipe


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagField(
        many=True,
        queryset=Tag.objects.all()
    )
    author = AuthorField(
        source='*'
    )
    ingredients = IngredientReadField(
        source='*'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):        
        return obj in self.context['request'].user.favorite_recipes.all()

    def get_is_in_shopping_cart(self, obj):
        return obj in self.context['request'].user.shoping_cart.recipes.all()