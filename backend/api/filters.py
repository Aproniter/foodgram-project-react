from rest_framework import filters

from recipes.models import Tag


class RecipeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        params = request.query_params
        is_favorited = params.get(
            "is_favorited", None
        )
        is_in_shopping_cart = params.get(
            "is_in_shopping_cart", None
        )
        tags = params.get(
            "tags", None
        )

        if is_favorited and int(params['is_favorited']):
            queryset = user.favorite_recipes.all()
        if is_in_shopping_cart and int(params['is_in_shopping_cart']):
            if hasattr(user.shoping_cart, 'recipes'):
                queryset = user.shoping_cart.recipes.all()
            else:
                queryset = {}
        if tags:
            tags = dict(**params)['tags']
            tags = Tag.objects.filter(
                slug__in=tags
            )
            queryset = queryset.filter(
                tags__in=tags
            )
        return queryset