from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter(
        field_name='author__id',
        lookup_expr='icontains'
    )
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='icontains'
    )
    is_favorited = filters.CharFilter(
        field_name='author.favorite_recipes',
        lookup_expr='icontains'
    )

    class Meta:
        model = Recipe
        fields = '__all__'