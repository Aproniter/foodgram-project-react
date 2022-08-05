from django_filters import FilterSet, CharFilter
from django_filters import NumberFilter

from recipes.models import Tag, Recipe


class RecipeFilterBackend(FilterSet):

    class Meta:
        model = Recipe
        fields = '__all__'

    @property
    def qs(self):
        queryset = super().qs
        user = getattr(self.request, 'user', None)
        is_favorited = self.request.GET.get('is_favorited')
        if is_favorited:
            queryset = queryset.filter(users=user)
        is_in_shopping_cart = self.request.GET.get('is_in_shopping_cart')
        if is_in_shopping_cart:
            queryset = queryset.filter(shoping_cart=user.shoping_cart)
        tags = list(self.request.GET.get('tags'))
        if tags:
            queryset = queryset.filter(tags__in=tags)
        return queryset