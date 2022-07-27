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


class RecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Recipe


class IngredientField(serializers.Field):

    def to_internal_value(self, data):
        print(data)
        # for i in data:
        #     # print(i)
        #     ingredient = Ingredient.objects.get(id=i['id'])
        #     print(ingredient)
        #     print(self)
        # return data

    # def to_representation(self, value):
    #     print(value)
    #     ret = [
    #         {
    #             'id': value.id,
    #             'amount': value.name,
    #         }
    #     ]
    #     return ret


class RecipeWriteSerializer(serializers.ModelSerializer):
    # ingredients = IngredientField(source='*')    
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    class Meta:
        fields = '__all__'
        model = Recipe
    
    def to_internal_value(self, data):
        print(data)
        print(self)
