# nutrition-journal
Purpose: Collaborate with a large-language model (LLM) to assist with food choices for optimal health.

Input: Copy narrative conversations from ChatGPT into Copilot with instructions to produce daily files with standardized nutritional information.     

Output: Feed the daily files through a YAML file in a Github workflow that calls a Python script which iterates through the files and populates tables with data at the Meals, Nutrients and Impacts levels.

Copilot instructions:

For each meal in the "List of Meals" section, please provide the following structured analysis.
Strictly follow these formatting rules for every meal:

Formatting Rules:

Every field MUST be present, even if unknown. Use “unknown” for missing values.
Dates MUST use YYYY-MM-DD format.
The "Ingredients" field MUST be a comma-separated list—no comments or extra text.
"Purines" MUST be one of: low, moderate, high, unknown (no comments or explanation in this field).
For each health condition, provide:
“Narrative:” followed by a brief assessment.
“Score:” as a single integer 1–10 (10 = best, 1 = worst).
Use bullet points (“•”) for each recommendation.
Separate each meal’s output with a line containing only three dashes (---).
Do NOT include any extra comments, formatting, or explanations outside this structure.
Structured Analysis Format:

Meal Date: [YYYY-MM-DD]
Meal Type: [Breakfast, Lunch, Dinner, Snack, Dessert, etc.]
Meal: [Meal description]
Ingredients: [comma-separated list, e.g. flour, blueberries, butter, sugar, olive oil]

Nutrient Estimate:
Calories: [value] kcal
Carbohydrates: [value] g
Sugar: [value] g
Fiber: [value] g
Protein: [value] g
Fat: [value] g
Saturated Fat: [value] g
Cholesterol: [value] mg
Sodium: [value] mg
Purines: [low/moderate/high/unknown]
Confidence: [score]/10

Health Impacts by Condition:

Fatty Liver
Narrative: [assessment]
Score: [1–10]

High Cholesterol
Narrative: [assessment]
Score: [1–10]

High Blood Pressure
Narrative: [assessment]
Score: [1–10]

Gout
Narrative: [assessment]
Score: [1–10]

Pre-diabetes
Narrative: [assessment]
Score: [1–10]

Recommendations:
• [Recommendation 1]
• [Recommendation 2]
• [etc.]

List of Meals:
7/26/25: Breakfast is a blueberry scone from La Provence Patisserie and Cafe.
7/26/25: Lunch is a macrobiotic addict salad from Kreation.

End of prompt. Please use this exact format for every meal.

Tables with sample records:

Meals:
MealID,DateID,MealTypeID,MealDescription,Ingredients
1,2025-06-21,Breakfast,"Grande drip coffee with nonfat milk and <¼ brown sugar; oatmeal with ~¼ brown sugar, fresh blueberries","coffee, nonfat milk, brown sugar, oats, blueberries"
2,2025-06-21,Lunch,"Mediterranean Protein Bowl: greens, lentils, tomatoes, avocado, egg, hummus, flax, wrap or pita","whole grain pita, mixed greens, cherry tomatoes, avocado, egg, hummus, lentils, flaxseed"

Nutrients:
NutrientID,MealID,NutrientType,Grams
1,1,Calories,260 kcal
2,1,Carbohydrates,50 g

Impacts:
ImpactID,MealID,ConditionType,Notes,Score
1,1,Fatty Liver,"Low-fat, high-fiber breakfast with minimal added sugar; supports liver health.",8
2,1,High Cholesterol,Low in saturated fat and cholesterol; beneficial for cholesterol management.,9
