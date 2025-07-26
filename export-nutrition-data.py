import os
import re
import glob
import datetime
import csv

# Always write CSVs to repo root (where this script is located)
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MEALS_CSV = os.path.join(REPO_ROOT, "Meals.csv")
NUTRIENTS_CSV = os.path.join(REPO_ROOT, "Nutrients.csv")
IMPACTS_CSV = os.path.join(REPO_ROOT, "Impacts.csv")
DAILY_FILES_DIR = "daily_files"

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
        print(f"parse_value: got empty or dash value '{val}', returning 0")
        return 0
    val = val.replace(',', '').replace(' ', '')
    range_match = re.match(r'[~<>=]?\s*(\d+)[–-](\d+)', val)
    if range_match:
        low = int(range_match.group(1))
        high = int(range_match.group(2))
        avg = (low + high) // 2
        print(f"parse_value: got range '{val}', returning average {avg}")
        return avg
    approx_match = re.match(r'~(\d+)', val)
    if approx_match:
        print(f"parse_value: got approx '{val}', returning {approx_match.group(1)}")
        return int(approx_match.group(1))
    ineq_match = re.match(r'[<>](\d+)', val)
    if ineq_match:
        print(f"parse_value: got inequality '{val}', returning {ineq_match.group(1)}")
        return int(ineq_match.group(1))
    num_match = re.search(r'(\d+)', val)
    if num_match:
        print(f"parse_value: got number '{val}', returning {num_match.group(1)}")
        return int(num_match.group(1))
    print(f"parse_value: did not match '{val}', returning 0")
    return 0

def extract_meal_description(section):
    h_blocks = list(re.finditer(r'^H:\s*(.*)', section, re.MULTILINE))
    l_blocks = list(re.finditer(r'^L:\s*(.*)', section, re.MULTILINE))
    print(f"extract_meal_description: found {len(h_blocks)} H: blocks and {len(l_blocks)} L: blocks.")
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
        print(f"extract_meal_description: summary after L: is '{summary}'")
        return summary
    elif h_blocks:
        result = h_blocks[-1].group(1).strip()
        print(f"extract_meal_description: summary after H: is '{result}'")
        return result
    print("extract_meal_description: no summary found")
    return ""

def extract_nutrients_from_section(section):
    nutrients = {}
    # Regex for "Nutrient: value" (with optional units)
    pattern_colon = re.compile(
        r'(?i)\b(' + '|'.join(re.escape(x) for x in NUTRIENT_SYNONYMS.keys()) + r')\b[:\s]+([<>=~]?\s*[\d,\.]+(?:[–\-][\d,\.]+)?)\s*(kcal|g|mg|mcg)?'
    )
    # Regex for "Nutrient value" in a Nutrition Estimate table
    pattern_table = re.compile(
        r'(?i)\b(' + '|'.join(re.escape(x) for x in NUTRIENT_SYNONYMS.keys()) + r')\b\s*[~:]*\s*([<>=~]?\s*[\d,\.]+(?:[–\-][\d,\.]+)?)\s*(kcal|g|mg|mcg)?'
    )

    for line in section.splitlines():
        # Try colon pattern first
        m = pattern_colon.search(line)
        if m:
            raw_name = m.group(1).lower()
            std_name = NUTRIENT_SYNONYMS.get(raw_name, raw_name.title())
            value = parse_value(m.group(2))
            if value != 0:
                nutrients[std_name] = value
                print(f"extract_nutrients_from_section: [colon] found '{raw_name}' as '{std_name}' with value '{value}' in line '{line}'")
            continue
        # Try table pattern next
        m = pattern_table.search(line)
        if m:
            raw_name = m.group(1).lower()
            std_name = NUTRIENT_SYNONYMS.get(raw_name, raw_name.title())
            value = parse_value(m.group(2))
            if value != 0:
                nutrients[std_name] = value
                print(f"extract_nutrients_from_section: [table] found '{raw_name}' as '{std_name}' with value '{value}' in line '{line}'")
    return nutrients

def assign_score(note):
    orig_note = note
    note = note.lower()
    if "excellent" in note or "totally safe" in note or "can help lower" in note or "low sodium" in note or "anti-inflammatory" in note or "good source" in note:
        print(f"assign_score: '{orig_note}' -> 10")
        return 10
    if "safe" in note and "not" not in note:
        print(f"assign_score: '{orig_note}' -> 10")
        return 10
    if "not ideal" in note or "spike" in note or "high" in note or "best as an occasional treat" in note or "not a daily item" in note:
        if "not ideal" in note:
            print(f"assign_score: '{orig_note}' -> 4")
            return 4
        if "best as an occasional treat" in note:
            print(f"assign_score: '{orig_note}' -> 2")
            return 2
        if "not a daily item" in note:
            print(f"assign_score: '{orig_note}' -> 3")
            return 3
        if "high sodium" in note:
            print(f"assign_score: '{orig_note}' -> 3")
            return 3
        if "spike" in note:
            print(f"assign_score: '{orig_note}' -> 3")
            return 3
        print(f"assign_score: '{orig_note}' -> 4")
        return 4
    if "okay in moderation" in note or "moderate" in note:
        print(f"assign_score: '{orig_note}' -> 5")
        return 5
    if "raise ldl" in note or "raise" in note:
        print(f"assign_score: '{orig_note}' -> 2")
        return 2
    if "no purines" in note:
        print(f"assign_score: '{orig_note}' -> 10")
        return 10
    print(f"assign_score: '{orig_note}' -> 7")
    return 7

CONDITION_MAP = {
    "Fatty liver": "Fatty Liver",
    "Pre-diabetes": "Pre-Diabetes",
    "High cholesterol": "High Cholesterol",
    "High blood pressure": "High Blood Pressure",
    "Gout": "Gout",
}

def parse_file(filepath):
    print(f"parse_file: parsing {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"parse_file: file content first 200 chars:\n{content[:200]}")
    date_match = re.search(r'RawLLM-(\d{8})$', filepath)
    if not date_match:
        print(f"parse_file: failed to find date in {filepath}")
        raise ValueError(f"Could not parse date from filename {filepath}")
    dateid = datetime.datetime.strptime(date_match.group(1), "%Y%m%d").date().isoformat()

    meal_sections = []
    current_mealtype = None
    current_section = []

    lines = content.splitlines()
    print(f"parse_file: total lines in file: {len(lines)}")
    for idx, line in enumerate(lines):
        raw = line.strip()
        normalized = raw.rstrip(':').lower()
        if normalized in MEAL_TYPES:
            print(f"parse_file: found meal type '{normalized}' at line {idx}")
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

    print(f"parse_file: meal_sections found: {len(meal_sections)}")
    meals = []
    for mealtype, section in meal_sections:
        meal_desc = extract_meal_description(section)
        if not meal_desc or len(meal_desc.split()) < 3:
            print(f"parse_file: skipping meal '{mealtype}' due to empty/short description: '{meal_desc}'")
            continue
        print(f"parse_file: meal '{mealtype}' description: '{meal_desc}'")
        meals.append({
            "DateID": dateid,
            "MealTypeID": mealtype,
            "MealDescription": meal_desc,
            "section": section,
        })

    print(f"parse_file: meals parsed: {len(meals)}")
    return meals

def extract_nutrients_impacts(meals, meal_id_start=1):
    nutrients = []
    impacts = []

    cond_line_re = re.compile(r'^(Fatty liver|Pre-diabetes|High cholesterol|High blood pressure|Gout)\s*([✅⚠️])\s*(.+)$', re.I | re.M)

    for idx, meal in enumerate(meals):
        meal_id = meal_id_start + idx
        section = meal["section"]

        print(f"extract_nutrients_impacts: extracting nutrients for meal_id {meal_id}, mealtype {meal['MealTypeID']}")
        nutrients_dict = extract_nutrients_from_section(section)
        for nut_name, nut_val in nutrients_dict.items():
            print(f"extract_nutrients_impacts: meal_id {meal_id} nutrient {nut_name} = {nut_val}")
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
            print(f"extract_nutrients_impacts: found Health Fit Check block for meal {meal_id}")
            for m in cond_line_re.finditer(fit_section):
                cond, fit, notes = m.group(1).strip(), m.group(2), m.group(3).strip()
                canonical_cond = CONDITION_MAP.get(cond, cond)
                score = assign_score(notes)
                print(f"extract_nutrients_impacts: impact for {canonical_cond}: {notes} score={score}")
                impacts.append({
                    "MealID": meal_id,
                    "ConditionType": canonical_cond,
                    "Notes": notes,
                    "Score": score,
                })
        notes_block = re.findall(r'Health Notes.*?\n(.+?)\n⸻', section, re.S)
        if notes_block:
            print(f"extract_nutrients_impacts: found Health Notes block for meal {meal_id}")
            for line in notes_block[0].splitlines():
                if ":" in line:
                    cond, notes = line.split(":", 1)
                    cond = cond.strip()
                    notes = notes.strip()
                    canonical_cond = CONDITION_MAP.get(cond, cond)
                    score = assign_score(notes)
                    print(f"extract_nutrients_impacts: impact for {canonical_cond}: {notes} score={score}")
                    impacts.append({
                        "MealID": meal_id,
                        "ConditionType": canonical_cond,
                        "Notes": notes,
                        "Score": score,
                    })

    print(f"extract_nutrients_impacts: total nutrients {len(nutrients)}, impacts {len(impacts)}")
    return nutrients, impacts

def main():
    files = sorted(glob.glob(os.path.join(DAILY_FILES_DIR, "RawLLM-*")))
    print("Files found:", files)
    all_meals = []
    all_nutrients = []
    all_impacts = []
    meal_id = 1

    for file in files:
        print(f"\n--- Processing file: {file} ---")
        meals = parse_file(file)
        for i, meal in enumerate(meals):
            meal['MealID'] = meal_id
            meal_id += 1
        nutrients, impacts = extract_nutrients_impacts(meals, meal_id_start=meal_id-len(meals))
        all_meals.extend(meals)
        all_nutrients.extend(nutrients)
        all_impacts.extend(impacts)

    print("Meals parsed:", len(all_meals))
    print("Nutrients extracted:", len(all_nutrients))
    print("Impacts extracted:", len(all_impacts))

    with open(MEALS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["MealID", "DateID", "MealTypeID", "MealDescription"])
        for meal in all_meals:
            print(f"Writing meal row: {meal['MealID']}, {meal['DateID']}, {meal['MealTypeID']}, {meal['MealDescription']}")
            writer.writerow([meal['MealID'], meal['DateID'], meal['MealTypeID'], meal['MealDescription']])

    with open(NUTRIENTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["NutrientID", "MealID", "NutrientType", "Grams"])
        for idx, nutrient in enumerate(all_nutrients, start=1):
            print(f"Writing nutrient row: {idx}, {nutrient['MealID']}, {nutrient['NutrientType']}, {nutrient['Grams']}")
            writer.writerow([idx, nutrient['MealID'], nutrient['NutrientType'], nutrient['Grams']])

    with open(IMPACTS_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ImpactID", "MealID", "ConditionType", "Notes", "Score"])
        for idx, impact in enumerate(all_impacts, start=1):
            print(f"Writing impact row: {idx}, {impact['MealID']}, {impact['ConditionType']}, {impact['Notes']}, {impact['Score']}")
            writer.writerow([idx, impact['MealID'], impact['ConditionType'], impact['Notes'], impact['Score']])

    print("Meals.csv written:", os.path.exists(MEALS_CSV))
    print("Nutrients.csv written:", os.path.exists(NUTRIENTS_CSV))
    print("Impacts.csv written:", os.path.exists(IMPACTS_CSV))
    print("Repo root used for output:", os.path.dirname(os.path.abspath(__file__)))
    print("Meals.csv absolute path:", MEALS_CSV)
    print("Nutrients.csv absolute path:", NUTRIENTS_CSV)
    print("Impacts.csv absolute path:", IMPACTS_CSV)

if __name__ == "__main__":
    main()
