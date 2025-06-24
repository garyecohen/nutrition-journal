# nutrition-journal
Purpose: Using LLM to assist with food choices

Method: Narrative conversion.  

Input: Human-computer exchange from another AI tool.  Copilot analyzes input to produce an output.  The input is a discussion of food intake.  

Output: Extract side by side the original desired meal and the eventually consumed meal following the discussion within.

Copilot instructions:
Give an input of narrative descriptions of what I planned to eat and what I actually ate, in natural language, produce the following output: 

For each meal on each day, a markdown table capturing: Date; Meal (Breakfast, Lunch, Dinner, Snack); Nutrient (Calories, Sugar, Carbohydrates, etc.); 
Desired Meal value (g); Consumed Meal value (g); Desired Meal Detail (free text); Consumed Meal Detail (free text) 

File Structure: Each day is logged in a separate markdown file named YYYY-MM-DD.md. A daily file contains tables (one per meal) with a row for each nutrient.

Sample Rows in a File:
Breakfast
Date	Meal	Nutrient	Desired Meal (g)	Consumed Meal (g)	Desired Meal Detail	Consumed Meal Detail
2025-06-22	Breakfast	Calories	250–300	~275	¾ cup Fage 0% Greek yogurt, ½ small banana, ⅓ cup blackberries, 2 tbsp granola	¾ cup Fage 0% Greek yogurt, ½ banana, ⅓ cup blackberries, 3 tbsp granola
2025-06-22	Breakfast	Protein	16–18	~17	Fage 0% Greek yogurt base (high protein, no fat), moderate granola	Fage 0% Greek yogurt base (high protein, no fat), moderate granola

Are you ready for the input?
