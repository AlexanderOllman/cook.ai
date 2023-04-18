import coles_vs_woolies.main as main
import coles_vs_woolies.search.woolies as woolies
import os
import openai
import time

openai.api_key = "OPEN-AI-KEY-HERE"

chat_history = []
chat_history.append({"role": "user", "content": "Based on ingredients known to be sold and easily available in Australia, think of 10 healthy, nutriciously rich recipes that take less than 10 minutes to prepare, serve two people, and share at least 70% of ingredients. Suggest the first recipe."})
initial = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages= chat_history
)

recipe = initial.choices[0].message
print(recipe.content)
chat_history.append(recipe)
chat_history.append({"role": "user", "content": "Give me the ingredients list as an array of strings. Do not provide any context, header, title or commentary, only the array. Do not include salt or pepper."})

completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=chat_history
)

ingredients = completion.choices[0].message.content
ingredients = ingredients.replace('"', "'")
ingredients = ingredients.split(", ")

items = []

for ingredient in ingredients:
    items.append(  {
    "raw": {
      "name": ingredient
    }
  },)

total = 0
response = woolies.ingredientsToProductsWoW(items)
for item in response['items']:
    print(item['product']['name'])
    total = total + (int(item['product']['quantity']['count']) * int(item['product']['price']['list']))

print("Total cost: " + str(total))
# ingredients = [  # Really helps to have weight/quantity
# 'olive oil',
# 'onion',
# 'garlic',
# 'ground cumin',
# 'smoked paprika',
# 'chili powder',
# 'dried oregano',
# 'black beans',
# 'cooked rice',
# 'flour tortillas',
# 'cheddar cheese',
# 'sour cream',
# 'avocado'
# ]
# print(ingredients)
# main.display(products=ingredients)
