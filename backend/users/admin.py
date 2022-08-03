from django.contrib import admin

from .models import User
from recipes.models import Recipe


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 1


class UserAdmin(admin.ModelAdmin):
    inlines = (RecipeInline,)


admin.site.register(User, UserAdmin)
