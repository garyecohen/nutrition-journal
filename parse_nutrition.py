import glob
import re

# Define patterns to extract nutrients from each meal section
MEALS = ['Breakfast', 'Lunch', 'Snack', 'Dinner']
NUTRIENTS = [
    'Calories', 'Total Sugar', 'Carbohydrates', 'Saturated Fat', 'Total Fat',
    'Protein', 'Fiber', 'Cholesterol', 'Sodium'
]

def parse_markdown_log(filename):
    result = {meal: {nutrient: 0 for nutrient in NUTRIENTS} for meal in MEALS}
    current_meal = None
    with open(filename, encoding='utf-8') as f:
        for line in f:
            match_meal = re.match(r'## (\w+)', line)
            if match_meal and match_meal.group(1) in MEALS:
                current_meal = match_meal.group(1)
            if current_meal:
                for nutrient in NUTRIENTS:
                    # Look for lines like: | ... | ... | ... | ... | value | ... |
                    match_nut = re.search(rf'\|\s*{nutrient}\s*\|[^|]*\|[^|]*\|[^|]*\|([^|]+)\|', line)
                    if match_nut:
                        value = match_nut.group(1).strip()
                        # Try to convert to float; ignore ranges or non-numeric
                        try:
                            if '-' in value or value == '':
                                continue
                            result[current_meal][nutrient] += float(value)
                        except ValueError:
                            continue
    return result

def main():
    log_files = glob.glob('202*-*-*.md')
    daily_summaries = {}

    for f in log_files:
        date = f.split('.')[0]
        summary = parse_markdown_log(f)
        daily_summaries[date] = summary

    # Write a summary report
    with open('nutrition_report.md', 'w', encoding='utf-8') as out:
        out.write('# Nutrition Report\n\n')
        for date, meals in sorted(daily_summaries.items()):
            out.write(f'## {date}\n')
            for meal, nutrients in meals.items():
                out.write(f'### {meal}\n')
                for n, v in nutrients.items():
                    out.write(f'- {n}: {v}\n')
                out.write('\n')

if __name__ == '__main__':
    main()
