import glob
import re
import os

print("Current working directory:", os.getcwd())

MEALS = ['Breakfast', 'Lunch', 'Snack', 'Dinner']
NUTRIENTS = [
    'Calories', 'Total Sugar', 'Carbohydrates', 'Saturated Fat', 'Total Fat',
    'Protein', 'Fiber', 'Cholesterol', 'Sodium', 'Sugar'
]

def parse_value(val):
    if not val or val.strip() in ('—', '-', ''):
        return 0
    val = val.replace(',', '').replace(' ', '')
    # Range: 500–700 or 500-700
    range_match = re.match(r'[~<>=]?\s*(\d+)[–-](\d+)', val)
    if range_match:
        low = int(range_match.group(1))
        high = int(range_match.group(2))
        return (low + high) // 2
    # Approximate: ~400
    approx_match = re.match(r'~(\d+)', val)
    if approx_match:
        return int(approx_match.group(1))
    # Inequality: <6 or >100
    ineq_match = re.match(r'[<>](\d+)', val)
    if ineq_match:
        return int(ineq_match.group(1))
    # Plain number anywhere in string
    num_match = re.search(r'(\d+)', val)
    if num_match:
        return int(num_match.group(1))
    return 0

def parse_log(filename):
    result = {meal: {nutrient: 0 for nutrient in NUTRIENTS} for meal in MEALS}
    current_meal = None
    with open(filename, encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if i < 20:
                print(f"[DEBUG] i={i}, line='{line}'")
            if line in MEALS:
                current_meal = line
                i += 2
                continue
            if current_meal and line and not line.startswith('Date'):
                if i < 20:
                    print(f"[DEBUG] Processing line under meal '{current_meal}': {repr(line)}")
                fields = line.split('\t')
                if len(fields) >= 5:
                    nutrient = fields[2].strip()
                    value_str = fields[4].strip()
                    if i < 20:
                        print(f"[DEBUG] Nutrient: {nutrient}, Value string: {value_str}")
                    if nutrient in NUTRIENTS:
                        value = parse_value(value_str)
                        if i < 20:
                            print(f"[DEBUG] Parsed value: {value}")
                        result[current_meal][nutrient] += value
            i += 1
    return result

def main():
    log_files = glob.glob('daily_files/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md')
    print("Looking for log files...")
    print("Found log files:", log_files)
    daily_summaries = {}

    for f in log_files:
        date = None
        # Try to find the date from filename or content
        m = re.match(r'(\d{4}-\d{2}-\d{2})\.md', f)
        if m:
            date = m.group(1)
        else:
            # fallback: get date from the first matching line in file
            with open(f, encoding='utf-8') as fd:
                for line in fd:
                    mm = re.match(r'(\d{4}-\d{2}-\d{2})', line)
                    if mm:
                        date = mm.group(1)
                        break
        summary = parse_log(f)
        if date:
            daily_summaries[date] = summary

    print("Parsed daily summaries:", daily_summaries)

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
