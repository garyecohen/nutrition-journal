Database upgrades
Break down table into:
  Nutrients: basically the same table without repeating the meal details
  Meals: add calculated condition scores for each (fatty liver = 7, gout = 6, etc)
  Structure to store reasoning for each condition score per meal

Separate tables for meals/nutrients

Date table (Quarter/Month/etc)
Meal table
Nutrient table
Condition table
Impact table?  What else from LLM output
Replace values in main tables with keys from above
