import os
import csv
import datetime
import re

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MEALS_CSV = os.path.join(REPO_ROOT, "Meals.csv")
NUTRIENTS_CSV = os.path.join(REPO_ROOT, "Nutrients.csv")
IMPACTS_CSV = os.path.join(REPO_ROOT, "Impacts.csv")
DAILY_FILES_DIR = "daily_files"

def iter_files(start, end):
    files = []
    d = start
    while d <= end:
        fname = os.path.join(DAILY_FILES_DIR, f"Input-{d.strftime('%Y%m%d')}")
        if os.path.exists(fname):
            files.append(fname)
        d += datetime.timedelta(days=1)
    return files

def parse_file(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip() for line in f]
    meals = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("Meal Date:"):
            meal = {
                "DateID": lines[i].split(":", 1)[1].strip(),
                "MealTypeID": "",
                "MealDescription": "",
                "Ingredients": "",
                "Nutrients": {},
                "Impacts": []
            }
            # Basic meal fields
            i += 1; meal["MealTypeID"] = lines[i].split(":", 1)[1].strip()
            i += 1; meal["MealDescription"] = lines[i].split(":", 1)[1].strip()
            i += 1; meal["Ingredients"] = lines[i].split(":", 1)[1].strip()
            # Nutrients
            i += 1  # skip 'Nutrient Estimate:'
            i += 1
            while i < len(lines) and lines[i] and ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                meal["Nutrients"][k.strip()] = v.strip()
                i += 1
            # Skip to 'Health Impacts by Condition:'
            while i < len(lines) and not lines[i].startswith("Health Impacts by Condition:"):
                i += 1
            i += 1  # skip header

            # Impacts (flexible parsing)
            while i < len(lines) and not lines[i].startswith("Recommendations:") and not lines[i].startswith("---"):
                line = lines[i].strip()
                # Skip blank lines
                if not line:
                    i += 1
                    continue
                # Try flexible parsing: either "Cond Narrative: ... Score: ..." on one line, or split across lines
                if re.match(r'^[A-Za-z ]+ Narrative:', line):
                    # Combined line: "Fatty Liver Narrative: ... Score: ..."
                    m = re.match(r'^([A-Za-z ]+) Narrative:(.*?)(Score:)(.*)', line)
                    if m:
                        cond = m.group(1).strip()
                        narrative = m.group(2).strip()
                        score = m.group(4).strip()
                        meal["Impacts"].append({
                            "ConditionType": cond,
                            "Notes": narrative,
                            "Score": score,
                        })
                        i += 1
                        continue
                elif re.match(r'^[A-Za-z ]+$', line):
                    # Condition name, look for Narrative and Score on next lines
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
        else:
            i += 1
    return meals

def main():
    start = datetime.date(2025, 6, 21)
    end = datetime.date(2025, 9, 18)
    files = iter_files(start, end)
    all_meals = []
    all_nutrients = []
    all_impacts = []
    meal_id = 1
    nutrient_id = 1
    impact_id = 1

    for file in files:
        meals = parse_file(file)
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

    with open(MEALS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MealID", "DateID", "MealTypeID", "MealDescription", "Ingredients"])
        writer.writerows(all_meals)

    with open(NUTRIENTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NutrientID", "MealID", "NutrientType", "Grams"])
        writer.writerows(all_nutrients)

    with open(IMPACTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ImpactID", "MealID", "ConditionType", "Notes", "Score"])
        writer.writerows(all_impacts)

if __name__ == "__main__":
    main()
