# nutrition-journal
Purpose: Using LLM to assist with food choices

Method: Narrative conversion.  

Input: Human-computer exchange from another AI tool.  Copilot analyzes input to produce an output.  The input is a discussion of food intake.  

Output: Extract side by side the original desired meal and the eventually consumed meal following the discussion within.

Copilot instructions:
Given an input of narrative descriptions of what I planned to eat and what I actually ate, in natural language, produce the following output:
For each meal on each day, a markdown table capturing: Date; Meal (Breakfast, Lunch, Dinner, Snack); Nutrient (Calories, Sugar, Carbohydrates, etc.); Desired Meal value (g); Consumed Meal value (g); Desired Meal Detail (free text); Consumed Meal Detail (free text)
File Structure: Each day is logged in a separate markdown file named YYYY-MM-DD.md. A daily file contains tables (one per meal) with a row for each nutrient.
I will input a file structure to mimic, followed by 3 input files for 7/7/25, 7/8/25, and 7/9/25.  Follow the input structure exactly, including the elimination of hashtags and pipes.

Are you ready for the 1st file (structure?)


NEW PROMPT:

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
