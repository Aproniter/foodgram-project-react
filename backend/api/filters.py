from django_filters import FilterSet, CharFilter
from django_filters import NumberFilter

from recipes.models import Tag, Recipe


class RecipeFilterBackend(FilterSet):
    tags = CharFilter(
        field_name='tags__slug',
    )

    class Meta:
        model = Recipe
        fields =('tags',)

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
        return queryset