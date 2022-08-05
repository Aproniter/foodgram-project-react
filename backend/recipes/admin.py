from django.contrib import admin

from .models import (
    Tag, Ingredient, IngredientAmount,
    Recipe, ShopingCart,
    
)
from users.models import User


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorites')
    search_fields = ('name', 'author__username', 'tags__slug')

    def in_favorites(self, obj):
        return obj.users.count()
    in_favorites.short_description = 'В избранном'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientAmount)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShopingCart)
