import os
import csv
import datetime
import re
# For debug
from datetime import datetime as datetime2
from collections import Counter

# Set up file paths and directories used in the script.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MEALS_CSV = os.path.join(REPO_ROOT, "Meals.csv")
NUTRIENTS_CSV = os.path.join(REPO_ROOT, "Nutrients.csv")
IMPACTS_CSV = os.path.join(REPO_ROOT, "Impacts.csv")
DAILY_FILES_DIR = "daily_files"

def iter_files(start, end):
    """
    Returns a list of daily input files within the date range.
    Only includes files that actually exist.
    Each file is expected to be named 'Input-YYYYMMDD' in DAILY_FILES_DIR.
    """
    files = []
    d = start
    while d <= end:
        fname = os.path.join(DAILY_FILES_DIR, f"Input-{d.strftime('%Y%m%d')}")
        if os.path.exists(fname):
            files.append(fname)
        d += datetime.timedelta(days=1)
    return files

def parse_file(path):
    """
    Parses a structured daily meal input file.
    Extracts all meals and their attributes (date, type, description, ingredients, nutrients, health impacts).
    Returns a list of meal dictionaries, one per meal in the file.
    """
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]
    meals = []
    i = 0
    while i < len(lines):
        print(f"DEBUG: Processing line {i}: {lines[i]!r}")  # Print every line as processed
        # Look for the start of a meal record
        if lines[i].startswith("Meal Date:"):
            try:
                meal = {
                    "DateID": lines[i].split(":", 1)[1].strip(),
                    "MealTypeID": "",
                    "MealDescription": "",
                    "Ingredients": "",
                    "Nutrients": {},
                    "Impacts": []
                }
            # Parse basic meal fields (type, description, ingredients)

            i += 1
            if not lines[i].startswith("Meal Type:"):
                print(f"DEBUG: Expected 'Meal Type:' at line {i} but got {lines[i]!r}")
            meal["MealTypeID"] = lines[i].split(":", 1)[1].strip()
            i += 1
            if not lines[i].startswith("Meal Description:"):
                print(f"DEBUG: Expected 'Meal Description:' at line {i} but got {lines[i]!r}")
            meal["MealDescription"] = lines[i].split(":", 1)[1].strip()
            i += 1
            if not lines[i].startswith("Ingredients:"):
                print(f"DEBUG: Expected 'Ingredients:' at line {i} but got {lines[i]!r}")
            meal["Ingredients"] = lines[i].split(":", 1)[1].strip()
            # Skip 'Nutrient Estimate:' header, then parse nutrients
            i += 1  # skip 'Nutrient Estimate:'
            i += 1
            while i < len(lines) and lines[i] and ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                meal["Nutrients"][k.strip()] = v.strip()
                i += 1
            # Advance to the 'Health Impacts by Condition:' section
            while i < len(lines) and not lines[i].startswith("Health Impacts by Condition:"):
                i += 1
            i += 1  # skip header

            # Parse health impacts for each condition (multiple formats supported)
            while i < len(lines) and not lines[i].startswith("Recommendations:") and not lines[i].startswith("---"):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                # Format 1: Combined line "Condition Narrative: ... Score: ..."
                m = re.match(r'^([A-Za-z ]+)\sNarrative:(.*?)Score:(.*)', line)
                if m:
                    cond = m.group(1).strip()
                    narrative = m.group(2).strip()
                    score = m.group(3).strip()
                    meal["Impacts"].append({
                        "ConditionType": cond,
                        "Notes": narrative,
                        "Score": score,
                    })
                    i += 1
                    continue
                # Format 2: Multi-line, with condition then narrative then score
                elif re.match(r'^[A-Za-z ]+$', line):
                    cond = line
                    i += 1
                    if i < len(lines) and lines[i].startswith("Narrative:"):
                        narrative = lines[i].split(":", 1)[1].strip()
                        i += 1
                    else:
                        narrative = ""
                    if i < len(lines) and lines[i].startswith("Score:"):
                        score = lines[i].split(":", 1)[1].strip()
                        i += 1
                    else:
                        score = ""
                    meal["Impacts"].append({
                        "ConditionType": cond,
                        "Notes": narrative,
                        "Score": score,
                    })
                    continue
                else:
                    i += 1
                    continue
            meals.append(meal)
            except Exception as e:
                    print(f"DEBUG: Exception when parsing meal starting at line {i}: {e}")
                    # You could also print a chunk of lines for context
            else:
                # If you expect a meal start here but don't get it, log why
                if "Meal Date" in lines[i]:
                    print(f"DEBUG: Line {i} contains 'Meal Date' but does not start a meal: {lines[i]!r}")
                i += 1
    return meals

def main():
    """
    Main execution function:
    - Defines date range for processing.
    - Iterates over each daily input file.
    - Parses meals and accumulates data for meals, nutrients, and impacts.
    - Writes resulting records into three CSV files for further analysis.
    """
    start = datetime.date(2025, 7, 30)
    end = datetime.date(2025, 7, 30)
    files = iter_files(start, end)
    all_meals = []
    all_nutrients = []
    all_impacts = []
    meal_id = 1
    nutrient_id = 1
    impact_id = 1

    for file in files:
        meals = parse_file(file)
        # For each meal in the parsed file, save meal, nutrient, and impact data with unique IDs
        for meal in meals:
            this_meal_id = meal_id
            all_meals.append([
                this_meal_id,
                meal["DateID"],
                meal["MealTypeID"],
                meal["MealDescription"],
                meal["Ingredients"]
            ])
            for nut, val in meal["Nutrients"].items():
                all_nutrients.append([nutrient_id, this_meal_id, nut, val])
                nutrient_id += 1
            for imp in meal["Impacts"]:
                all_impacts.append([
                    impact_id,
                    this_meal_id,
                    imp["ConditionType"],
                    imp["Notes"],
                    imp["Score"]
                ])
                impact_id += 1
            meal_id += 1

    # Debug: print meals per date in M/D format
    date_counts = Counter(meal[1] for meal in all_meals)  # meal[1] is DateID
    for date, count in date_counts.items():
        dt = datetime2.strptime(date, "%Y-%m-%d")
        print(f"{dt.month}/{dt.day} - {count}")

    # Write meals summary to Meals.csv
    with open(MEALS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MealID", "DateID", "MealTypeID", "MealDescription", "Ingredients"])
        writer.writerows(all_meals)

    # Write nutrients data to Nutrients.csv
    with open(NUTRIENTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NutrientID", "MealID", "NutrientType", "Grams"])
        writer.writerows(all_nutrients)

    # Write health impact assessments to Impacts.csv
    with open(IMPACTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ImpactID", "MealID", "ConditionType", "Notes", "Score"])
        writer.writerows(all_impacts)

if __name__ == "__main__":
    # Script entry point: runs the main function if called directly.
    main()
