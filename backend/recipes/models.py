from django.db import models
from django.core.validators import MinValueValidator

class Tag(models.Model):
    name = models.CharField(
        verbose_name='Тег',
        max_length=255
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=255
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        db_index=True,
        max_length=255
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=255
    )    
    measurement_unit = models.CharField(
        verbose_name='Еденица измерения',
        max_length=255
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        'Recipe',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    amount = models.IntegerField()


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Рецепт',
        max_length=200
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(0),
        ),
        error_messages={
            'validators': 'Время приготовления не может быть меньше 0'
            }
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги',
        related_name='recipes',
        blank=True,
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
        blank=True
    )
    image = models.TextField(
        verbose_name='Изображение',
        blank=True,
    )
    author = models.ForeignKey(
        verbose_name='Автор',
        to='users.User',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ShopingCart(models.Model):
    recipes = models.ManyToManyField(
        'Recipe',
        verbose_name='Рецепты',
        related_name='shoping_cart',
        blank=True,
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    # def __str__(self):
    #     return self.user