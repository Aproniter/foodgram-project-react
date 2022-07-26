from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (    
    UsersViewSet, TagViewSet, RecipeViewSet, IngredientViewSet,
    registration, get_token
)

app_name = 'api'

router = SimpleRouter()
router.register('^users', UsersViewSet, basename='users')

router.register(    
    'tags',
    TagViewSet,
    basename='tags',
)

router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)

router.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

urlpatterns = [
    path(
        'users/',
        registration,
        name='registration'
    ),
    path('auth/token/login/', get_token, name='get_token'),
    path('', include(router.urls)),
]