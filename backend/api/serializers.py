import re

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.core.exceptions import ValidationError

from users.models import User
from recipes.models import Tag, Recipe, Ingredient


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
        fields = ('token',)

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


class IsSubscribed(serializers.Field):

    def to_representation(self, value):
        return True


class Recipes(serializers.Field):

    def to_representation(self, value):
        return value.recipes


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = IsSubscribed(source='*')
    recipes = Recipes(source='*')

    class Meta:
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes'   
        )
        model = User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'    
        model = Tag


class RecipeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Recipe


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'    
        model = Ingredient
