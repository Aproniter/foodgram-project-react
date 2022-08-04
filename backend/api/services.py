from django.db.models import Sum, Count, Subquery, OuterRef

from recipes.models import Ingredient, IngredientAmount


def get_file(shopping_cart):
    ingredients = Ingredient.objects.filter(
        recipes__in=shopping_cart.recipes.all()
    ).annotate(
        amount=Sum('recipes__ingredientamount__amount')
    )
    with open('shopping-list.txt', 'w') as file:
        for i in ingredients:
            file.write(
                f'{i.name} - {i.amount} {i.measurement_unit}\n'
            )
    send_file = open('shopping-list.txt','rb')
    return send_file