from collections import Counter

from recipes.models import IngredientAmount

def get_file(shopping_cart):
    ingredients = [
        {j: IngredientAmount.objects.get(
            recipe=i, ingredient=j
        ).amount for j in i.ingredients.all()} 
        for i in shopping_cart.recipes.all()
    ]
    shoping_list = Counter()
    for ingredient in ingredients:
        shoping_list.update(ingredient)
    with open('shopping-list.txt', 'w') as file:
        for ingredient in shoping_list:
            count = shoping_list[ingredient]
            file.write(
                f'{ingredient.name} - {count} {ingredient.measurement_unit}\n'
            )
    send_file = open('shopping-list.txt','rb')
    return send_file