import os
import re
import glob
import datetime
import csv

# Directory containing the daily_files
DAILY_FILES_DIR = "daily_files"

# Output CSV files
MEALS_CSV = "Meals.csv"
NUTRIENTS_CSV = "Nutrients.csv"
IMPACTS_CSV = "Impacts.csv"

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]

# Helper for extracting the best meal description from a meal section
def extract_meal_description(section):
    """
    Extract a concise, accurate meal description from a meal section.

    Logic:
    - Prefer the LLM response (L:) after the last 'H:' (user) meal report, as this is usually an analysis/summary.
    - If not found, fallback to the last L: block.
    - If no L: block, fallback to the last H: block.
    - Clean the result for excessive markdown, lines, or ASCII art.
    """
    # Find all 'H:' (user) and 'L:' (LLM) lines and their positions
    h_blocks = list(re.finditer(r'^H:\s*(.*)', section, re.MULTILINE))
    l_blocks = list(re.finditer(r'^L:\s*(.*)', section, re.MULTILINE))

    if h_blocks:
        last_h = h_blocks[-1]
        # Find the first L: after last H:
        l_after_h = [l for l in l_blocks if l.start() > last_h.end()]
        if l_after_h:
            last_l = l_after_h[0]
        elif l_blocks:
            last_l = l_blocks[-1]
        else:
            last_l = None
    elif l_blocks:
        last_l = l_blocks[-1]
    else:
        last_l = None

    # Now extract the paragraph following last_l
    if last_l:
        # Grab everything after this L: line, or just this line if nothing follows
        after = section[last_l.end():]
        # Get up to first double newline or horizontal line (⸻), or end
        summary = after.split("\n\n")[0].split("⸻")[0].strip()
        # If empty, fallback to just the L: line
        if not summary:
            summary = last_l.group(1).strip()
        # Clean up markdown or ASCII separators
        summary = re.sub(r'^[-•⸻]+$', '', summary, flags=re.MULTILINE).strip()
        return summary
    elif h_blocks:
        # Fallback to last H: block content
        return h_blocks[-1].group(1).strip()
    return ""

# Helper: Convert mg to g
def mg_to_g(val):
    try:
        return float(val) / 1000
    except Exception:
        return val

# Helper: Extract highest value from range or return value as float
def extract_highest(val):
    if isinstance(val, (float, int)):
        return float(val)
    if isinstance(val, str):
        if "–" in val or "-" in val:
            val = val.replace("–", "-")
            parts = re.split(r"[-]", val)
            try:
                return float(parts[-1].strip())
            except Exception:
                pass
        try:
            return float(val.strip())
        except Exception:
            pass
    return None

# Helper: Assign score based on keywords
def assign_score(note):
    note = note.lower()
    if "excellent" in note or "totally safe" in note or "can help lower" in note or "low sodium" in note or "anti-inflammatory" in note or "good source" in note:
        return 10
    if "safe" in note and "not" not in note:
        return 10
    if "not ideal" in note or "spike" in note or "high" in note or "best as an occasional treat" in note or "not a daily item" in note:
        if "not ideal" in note:
            return 4
        if "best as an occasional treat" in note:
            return 2
        if "not a daily item" in note:
            return 3
        if "high sodium" in note:
            return 3
        if "spike" in note:
            return 3
        return 4
    if "okay in moderation" in note or "moderate" in note:
        return 5
    if "raise ldl" in note or "raise" in note:
        return 2
    if "no purines" in note:
        return 10
    return 7

# Mapping for condition types to canonical names
CONDITION_MAP = {
    "Fatty liver": "Fatty Liver",
    "Pre-diabetes": "Pre-Diabetes",
    "Pre-diabetes": "Pre-Diabetes",
    "High cholesterol": "High Cholesterol",
    "High blood pressure": "High Blood Pressure",
    "Gout": "Gout",
}

def parse_file(filepath):
    # Parse a single RawLLM file and return extracted Meals, Nutrients, and Impacts
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    date_match = re.search(r'RawLLM-(\d{8})$', filepath)
    if not date_match:
        raise ValueError(f"Could not parse date from filename {filepath}")
    dateid = datetime.datetime.strptime(date_match.group(1), "%Y%m%d").date().isoformat()

    # Split content by meal type headers
    meal_sections = []
    current_mealtype = None
    current_section = []

    lines = content.splitlines()
    for idx, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped in MEAL_TYPES:
            if current_mealtype is not None and current_section:
                meal_sections.append((current_mealtype, "\n".join(current_section)))
                current_section = []
            current_mealtype = line_stripped
        elif line_stripped == "" and not current_section:
            continue
        else:
            current_section.append(line)
    if current_mealtype and current_section:
        meal_sections.append((current_mealtype, "\n".join(current_section)))

    meals = []
    for mealtype, section in meal_sections:
        meal_desc = extract_meal_description(section)
        # Skip sections where no plausible meal description can be found
        if not meal_desc or len(meal_desc.split()) < 3:
            continue
        meals.append({
            "DateID": dateid,
            "MealTypeID": mealtype,
            "MealDescription": meal_desc,
            "section": section,  # Keep for further parsing
        })

    return meals

def extract_nutrients_impacts(meals, meal_id_start=1):
    nutrients = []
    impacts = []

    # Nutrient field mapping: (user-facing label, canonical label, units)
    NUTRIENT_MAPPINGS = {
        "Calories": ("Calories", "kcal"),
        "Carbs": ("Carbohydrates", "g"),
        "Carbohydrates": ("Carbohydrates", "g"),
        "Fiber": ("Fiber", "g"),
        "Sugars": ("Sugars", "g"),
        "Protein": ("Protein", "g"),
        "Fat": ("Fat", "g"),
        "Sodium": ("Sodium", "mg"),
        "Sugar": ("Sugars", "g"),
        "Saturated Fat": ("Saturated Fat", "g"),
    }

    # Regexes for nutrients
    nutrient_line_re = re.compile(r'^(Calories|Carbs|Carbohydrates|Fiber|Sugars|Sugar|Protein|Fat|Sodium|Saturated Fat)\s*~?([-\d\.–]+)(?:\s*\((?:includes|with)[^\)]*\))?', re.I)
    gram_val_re = re.compile(r'~?([-\d\.–]+)\s*g', re.I)
    cal_val_re = re.compile(r'~?([-\d\.–]+)\s*k?cal', re.I)
    mg_val_re = re.compile(r'~?([-\d\.–]+)\s*mg', re.I)

    # ConditionType regex
    cond_line_re = re.compile(r'^(Fatty liver|Pre-diabetes|High cholesterol|High blood pressure|Gout)\s*([✅⚠️])\s*(.+)$', re.I | re.M)

    for idx, meal in enumerate(meals):
        meal_id = meal_id_start + idx
        section = meal["section"]

        # --- Nutrients Extraction ---
        # Find Nutrition Estimate or similar block
        nutri_blocks = re.findall(r'Nutrition Estimate:(.+?)(?:⸻|$)', section, re.S)
        if not nutri_blocks:
            nutri_blocks = re.findall(r'Estimated Nutrition:(.+?)(?:⸻|$)', section, re.S)
        if not nutri_blocks:
            nutri_blocks = re.findall(r'Estimated Nutritional Info(.+?)(?:⸻|$)', section, re.S)
        if not nutri_blocks:
            nutri_blocks = re.findall(r'Snack:(.+?)(?:⸻|$)', section, re.S)
        if not nutri_blocks:
            nutri_blocks = re.findall(r'Nutrient\s*Approx\.?\s*Amount(.+?)(?:⸻|$)', section, re.S)

        for block in nutri_blocks:
            for line in block.splitlines():
                line = line.strip()
                m = nutrient_line_re.match(line)
                if m:
                    label, val = m.group(1), m.group(2)
                    label = label.strip()
                    canonical, units = NUTRIENT_MAPPINGS.get(label, (label, "g"))
                    if not canonical:
                        continue
                    if units == "mg":
                        grams_val = mg_to_g(extract_highest(val))
                    else:
                        grams_val = extract_highest(val)
                    nutrients.append({
                        "MealID": meal_id,
                        "NutrientType": canonical,
                        "Grams": grams_val,
                    })
                elif "Calories" in line:
                    m = cal_val_re.search(line)
                    if m:
                        val = m.group(1)
                        nutrients.append({
                            "MealID": meal_id,
                            "NutrientType": "Calories",
                            "Grams": extract_highest(val),
                        })
                elif "Sodium" in line:
                    m = mg_val_re.search(line)
                    if m:
                        val = m.group(1)
                        nutrients.append({
                            "MealID": meal_id,
                            "NutrientType": "Sodium",
                            "Grams": mg_to_g(extract_highest(val)),
                        })

        # --- Impacts Extraction ---
        # Look for Health Fit Check or Health Notes
        fit_section = None
        fit_start = section.find("Health Fit Check:")
        if fit_start >= 0:
            fit_end = section.find("⸻", fit_start)
            fit_section = section[fit_start:fit_end if fit_end > 0 else None]
            for m in cond_line_re.finditer(fit_section):
                cond, fit, notes = m.group(1).strip(), m.group(2), m.group(3).strip()
                canonical_cond = CONDITION_MAP.get(cond, cond)
                score = assign_score(notes)
                impacts.append({
                    "MealID": meal_id,
                    "ConditionType": canonical_cond,
                    "Notes": notes,
                    "Score": score,
                })
        notes_block = re.findall(r'Health Notes.*?\n(.+?)\n⸻', section, re.S)
        if notes_block:
            for line in notes_block[0].splitlines():
                if ":" in line:
                    cond, notes = line.split(":", 1)
                    cond = cond.strip()
                    notes = notes.strip()
                    canonical_cond = CONDITION_MAP.get(cond, cond)
                    score = assign_score(notes)
                    impacts.append({
                        "MealID": meal_id,
                        "ConditionType": canonical_cond,
                        "Notes": notes,
                        "Score": score,
                    })

    return nutrients, impacts

def main():
    # Find all files matching pattern
    files = sorted(glob.glob(os.path.join(DAILY_FILES_DIR, "RawLLM-*")))
    all_meals = []
    all_nutrients = []
    all_impacts = []
    meal_id = 1

    for file in files:
        meals = parse_file(file)
        for i, meal in enumerate(meals):
            meal['MealID'] = meal_id
            meal_id += 1
        nutrients, impacts = extract_nutrients_impacts(meals, meal_id_start=meal_id-len(meals))
        all_meals.extend(meals)
        all_nutrients.extend(nutrients)
        all_impacts.extend(impacts)

    # Write Meals table
    with open(MEALS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MealID", "DateID", "MealTypeID", "MealDescription"])
        for meal in all_meals:
            writer.writerow([meal['MealID'], meal['DateID'], meal['MealTypeID'], meal['MealDescription']])

    # Write Nutrients table
    with open(NUTRIENTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NutrientID", "MealID", "NutrientType", "Grams"])
        for idx, nutrient in enumerate(all_nutrients, start=1):
            writer.writerow([idx, nutrient['MealID'], nutrient['NutrientType'], nutrient['Grams']])

    # Write Impacts table
    with open(IMPACTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ImpactID", "MealID", "ConditionType", "Notes", "Score"])
        for idx, impact in enumerate(all_impacts, start=1):
            writer.writerow([idx, impact['MealID'], impact['ConditionType'], impact['Notes'], impact['Score']])

if __name__ == "__main__":
    main()
