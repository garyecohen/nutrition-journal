Version 1 - Data is useful to me (reports, charts etc)
Version 2 - Data can be input by others

Database upgrades
Break down table into:
  Nutrients: basically the same table without repeating the meal details
  Meals: add calculated condition scores for each (fatty liver = 7, gout = 6, etc)
  Structure to store reasoning for each condition score per meal
  Ingredients for each meal?

Create the series of prompts for Copilot to create the tables.

Separate tables for meals/nutrients

Date table (Quarter/Month/etc)
Meal table
Nutrient table
Condition table
Impact table?  What else from LLM output
Replace values in main tables with keys from above

Could get more useful data in LLM file by refining prompt (Asking for specific suggestions at a specific granularity) - Suggestion Table
