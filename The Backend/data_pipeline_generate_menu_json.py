import csv
import json
import os

# Configuration: Update this if your file is named differently!
INPUT_CSV = 'main.csv'
OUTPUT_JSON = 'menu.json'

def load_csv_data(filepath):
    data = []
    if not os.path.exists(filepath):
        print(f"CRITICAL ERROR: File '{filepath}' not found.")
        print("Please ensure your CSV file is in the same folder and named correctly.")
        return []
    
    print(f"--- Reading {filepath} ---")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        try:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if headers:
                print(f"DEBUG: Raw Headers found in CSV: {headers}")
                clean_headers = [h.strip() for h in headers]
                print(f"DEBUG: Cleaned Headers: {clean_headers}")
                reader.fieldnames = clean_headers
            else:
                print("CRITICAL ERROR: No headers found. Is the file empty?")
                return []
            
            for i, row in enumerate(reader):
                clean_row = {k.strip(): v for k, v in row.items() if k}
                data.append(clean_row)
                if i == 0:
                    print(f"DEBUG: First Row Data: {clean_row}")
        except Exception as e:
            print(f"CRITICAL ERROR reading CSV: {e}")
            return []
            
    print(f"DEBUG: Total rows read: {len(data)}")
    return data

def get_col(row, candidates, default=''):
    """Helper: Tries multiple column names to find data."""
    for col in candidates:
        if col in row:
            val = row[col]
            if val: return val
    return default

def clean_price(val):
    """Helper: Converts string price to float safely."""
    if not val: 
        return 0.0
    try:
        return float(val.replace('$', '').strip())
    except ValueError:
        return 0.0

def build_menu_from_main():
    print(f"--- Starting Menu Build ---")
    
    raw_rows = load_csv_data(INPUT_CSV)
    if not raw_rows:
        print("Stopping: No data to process.")
        return

    # Dictionary to hold unique menu items. 
    # Key will be the generated Name (e.g. "Burger Meal" vs "Burger A La Carte")
    menu_items = {}

    for row in raw_rows:
        # 1. Identify the Core Item Name
        core_name = get_col(row, ['ItemName', 'Original_ItemName', 'Item Name', 'Name']).strip()
        
        if not core_name:
            continue

        # Extract shared data
        item_id = get_col(row, ['ItemID', 'Original_ItemID', 'ID'])
        description = get_col(row, ['Description', 'Desc'])
        category = get_col(row, ['Category'], 'Lunch')
        
        tags_raw = get_col(row, ['Tags', 'tags'])
        tags = [t.strip() for t in tags_raw.replace('|', ',').split(',') if t.strip()]

        comps_raw = get_col(row, ['Meal_Components', 'Components', 'Meal Components'])
        comp_ids = [c.strip() for c in comps_raw.split('|') if c.strip()]

        # Extract Prices
        base_price_val = get_col(row, ['Base_Price', 'BasePrice', 'Price'])
        meal_price_val = get_col(row, ['Meal_Price', 'MealPrice', 'MenuPrice'])
        
        base_price = clean_price(base_price_val)
        meal_price = clean_price(meal_price_val)

        # --- LOGIC: CREATE UP TO TWO ITEMS ---
        
        # 1. Create Meal Version (if price exists)
        if meal_price > 0:
            # If the core name doesn't already say "Meal", append it for clarity
            meal_name = core_name
            if "Meal" not in core_name and "Plate" not in core_name:
                meal_name = f"{core_name} Meal"

            if meal_name not in menu_items:
                menu_items[meal_name] = {
                    "id": item_id, # Same ID, different variations handled by name/price
                    "name": meal_name,
                    "description": description,
                    "price": meal_price,
                    "category": category,
                    "type": "Meal",
                    "tags": tags + ["Meal"],
                    "component_ids": comp_ids, # Meals have components (sides)
                    "suggested_substitutions": []
                }
            
            # Add substitutions to this specific variant
            add_substitution(row, menu_items[meal_name])

        # 2. Create A La Carte Version (if price exists)
        if base_price > 0:
            # Construct A La Carte Name
            # If it's a side or drink, just use the name. If it's a main, add "(A La Carte)"
            is_side_or_drink = "Side" in category or "Drink" in category or "Beverage" in category
            
            if is_side_or_drink:
                alc_name = core_name
            else:
                alc_name = f"{core_name} (A La Carte)"

            if alc_name not in menu_items:
                menu_items[alc_name] = {
                    "id": f"{item_id}-ALC", # Create a distinct ID suffix
                    "name": alc_name,
                    "description": description, # Could modify desc here if needed
                    "price": base_price,
                    "category": category,
                    "type": "A La Carte",
                    "tags": [t for t in tags if t != "Meal"], # Remove "Meal" tag if present
                    "component_ids": [], # A La Carte usually has no side components
                    "suggested_substitutions": []
                }
            
            # Add substitutions to this specific variant
            add_substitution(row, menu_items[alc_name])

    # 4. Save
    menu_structure = {
        "menu": {
            "breakfast": [],
            "lunch": []
        }
    }

    count = 0
    for item in menu_items.values():
        count += 1
        cat = item['category'].lower()
        if 'breakfast' in cat:
            menu_structure['menu']['breakfast'].append(item)
        else:
            menu_structure['menu']['lunch'].append(item)

    if count == 0:
        print("WARNING: Script finished but found 0 valid menu items.")
    else:
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(menu_structure, f, indent=2)
        print(f"--- Success! Generated {OUTPUT_JSON} with {count} items. ---")

def add_substitution(row, item_obj):
    """Helper to append substitutions to a menu item object."""
    sub_name = get_col(row, ['SubstituteName', 'Substitute_ItemName', 'Substitute Name']).strip()
    
    if sub_name:
        sub_entry = {
            "trigger_ingredient": get_col(row, ['Category'], 'General'),
            "suggest_item_id": get_col(row, ['Substitute_ID', 'SubstituteID']),
            "suggest_item_name": sub_name,
            "rag_justification": get_col(row, ['RAG_Justification', 'Justification', 'RAG Justification'])
        }
        
        existing_subs = [s['suggest_item_name'] for s in item_obj['suggested_substitutions']]
        if sub_name not in existing_subs:
            item_obj['suggested_substitutions'].append(sub_entry)

if __name__ == "__main__":
    build_menu_from_main()