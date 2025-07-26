import os
import re
import glob
import datetime
import csv

DAILY_FILES_DIR = "daily_files"
MEALS_CSV = "Meals.csv"
NUTRIENTS_CSV = "Nutrients.csv"
IMPACTS_CSV = "Impacts.csv"

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "dessert"]

NUTRIENT_SYNONYMS = {
    "calories": "Calories",
    "total sugar": "Sugar",
    "sugar": "Sugar",
    "carbohydrates": "Carbohydrates",
    "carbs": "Carbohydrates",
    "saturated fat": "Saturated Fat",
    "total fat": "Fat",
    "fat": "Fat",
    "protein": "Protein",
    "fiber": "Fiber",
    "cholesterol": "Cholesterol",
    "sodium": "Sodium",
}

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

def extract_meal_description(section):
    h_blocks = list(re.finditer(r'^H:\s*(.*)', section, re.MULTILINE))
    l_blocks = list(re.finditer(r'^L:\s*(.*)', section, re.MULTILINE))
    if h_blocks:
        last_h = h_blocks[-1]
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

    if last_l:
        after = section[last_l.end():]
        summary = after.split("\n\n")[0].split("⸻")[0].strip()
        if not summary:
            summary = last_l.group(1).strip()
        summary = re.sub(r'^[-•⸻]+$', '', summary, flags=re.MULTILINE).strip()
        return summary
    elif h_blocks:
        return h_blocks[-1].group(1).strip()
    return ""

def extract_nutrients_from_section(section):
    """
    Extract nutrients from any line in a meal section that looks like
    'NutrientName: value unit' or 'NutrientName value unit', robust to format.
    Also handles 'value unit NutrientName' format like '26g protein'.
    Returns a dict {CanonicalNutrientName: value}
    """
    nutrients = {}
    
    # Pattern 1: Nutrient followed by value (e.g., "Calories ~720", "Fat ~36g")
    pattern1 = re.compile(
        r'(?i)\b(' + '|'.join(re.escape(x) for x in NUTRIENT_SYNONYMS.keys()) + r')\b[:\s~\-]*([<>=~]?\s*[\d,\.]+(?:[–\-][\d,\.]+)?)\s*(kcal|g|mg|mcg)?',
        re.I
    )
    
    # Pattern 2: Value followed by nutrient (e.g., "26g protein", "760mg sodium")
    pattern2 = re.compile(
        r'(?i)([<>=~]?\s*[\d,\.]+(?:[–\-][\d,\.]+)?)\s*(g|mg|mcg|kcal)?\s+(' + '|'.join(re.escape(x) for x in NUTRIENT_SYNONYMS.keys()) + r')\b',
        re.I
    )
    
    for line in section.splitlines():
        # Try pattern 1 (nutrient followed by value)
        for m in pattern1.finditer(line):
            raw_name = m.group(1).lower()
            std_name = NUTRIENT_SYNONYMS.get(raw_name, raw_name.title())
            value = parse_value(m.group(2))
            # Store the higher value if we've seen this nutrient before
            if std_name not in nutrients or value > nutrients[std_name]:
                nutrients[std_name] = value
                
        # Try pattern 2 (value followed by nutrient)
        for m in pattern2.finditer(line):
            raw_name = m.group(3).lower()
            std_name = NUTRIENT_SYNONYMS.get(raw_name, raw_name.title())
            value = parse_value(m.group(1))
            # Store the higher value if we've seen this nutrient before
            if std_name not in nutrients or value > nutrients[std_name]:
                nutrients[std_name] = value
                
    return nutrients

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

CONDITION_MAP = {
    "Fatty liver": "Fatty Liver",
    "Pre-diabetes": "Pre-Diabetes",
    "Pre-diabetes": "Pre-Diabetes",
    "High cholesterol": "High Cholesterol",
    "High blood pressure": "High Blood Pressure",
    "Gout": "Gout",
}

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    date_match = re.search(r'RawLLM-(\d{8})$', filepath)
    if not date_match:
        raise ValueError(f"Could not parse date from filename {filepath}")
    dateid = datetime.datetime.strptime(date_match.group(1), "%Y%m%d").date().isoformat()

    meal_sections = []
    current_mealtype = None
    current_section = []

    lines = content.splitlines()
    for idx, line in enumerate(lines):
        raw = line.strip()
        normalized = raw.rstrip(':').lower()
        if normalized in MEAL_TYPES:
            if current_mealtype is not None and current_section:
                meal_sections.append((current_mealtype, "\n".join(current_section)))
                current_section = []
            current_mealtype = normalized.capitalize()
        elif raw == "" and not current_section:
            continue
        else:
            current_section.append(line)
    if current_mealtype and current_section:
        meal_sections.append((current_mealtype, "\n".join(current_section)))

    meals = []
    for mealtype, section in meal_sections:
        meal_desc = extract_meal_description(section)
        if not meal_desc or len(meal_desc.split()) < 3:
            continue
        meals.append({
            "DateID": dateid,
            "MealTypeID": mealtype,
            "MealDescription": meal_desc,
            "section": section,
        })

    return meals

def extract_nutrients_impacts(meals, meal_id_start=1):
    nutrients = []
    impacts = []

    cond_line_re = re.compile(r'^(Fatty liver|Pre-diabetes|High cholesterol|High blood pressure|Gout)\s*([✅⚠️])\s*(.+)$', re.I | re.M)

    for idx, meal in enumerate(meals):
        meal_id = meal_id_start + idx
        section = meal["section"]

        # --- Nutrients Extraction ---
        nutrients_dict = extract_nutrients_from_section(section)
        for nut_name, nut_val in nutrients_dict.items():
            nutrients.append({
                "MealID": meal_id,
                "NutrientType": nut_name,
                "Grams": nut_val,
            })

        # --- Impacts Extraction ---
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

    with open(MEALS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MealID", "DateID", "MealTypeID", "MealDescription"])
        for meal in all_meals:
            writer.writerow([meal['MealID'], meal['DateID'], meal['MealTypeID'], meal['MealDescription']])

    with open(NUTRIENTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NutrientID", "MealID", "NutrientType", "Grams"])
        for idx, nutrient in enumerate(all_nutrients, start=1):
            writer.writerow([idx, nutrient['MealID'], nutrient['NutrientType'], nutrient['Grams']])

    with open(IMPACTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ImpactID", "MealID", "ConditionType", "Notes", "Score"])
        for idx, impact in enumerate(all_impacts, start=1):
            writer.writerow([idx, impact['MealID'], impact['ConditionType'], impact['Notes'], impact['Score']])

if __name__ == "__main__":
    main()
