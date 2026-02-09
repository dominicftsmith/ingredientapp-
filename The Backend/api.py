import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
import json
import csv
import os
from datetime import datetime

# --------------------------------------------------------------------------
# Configuration & Constants
# --------------------------------------------------------------------------
CHROMA_DB_PATH = "./chroma_db"
INVENTORY_CSV_PATH = "inventory_lots.csv"
THRESHOLDS_CSV_PATH = "ingredients.csv"  # New config file

# Default fallback if an item isn't in the CSV
DEFAULT_LOW_THRESHOLD = 15.0

# --------------------------------------------------------------------------
# Helper Functions: Configuration Loading
# --------------------------------------------------------------------------
def load_thresholds_from_csv(file_path: str) -> Dict[str, float]:
    """
    Loads specific low-stock thresholds from a CSV file.
    Expected columns: 'Ingredient' and 'Threshold' (or similar).
    """
    thresholds = {}
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: Thresholds file '{file_path}' not found. Using defaults.")
        return thresholds

    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            # Smart Column Detection
            # Looks for: "Ingredient", "Name", "Item"
            name_col = next((h for h in headers if any(x in h.lower() for x in ['ingredient', 'name', 'item'])), None)
            # Looks for: "Threshold", "Low", "Min", "Limit"
            val_col = next((h for h in headers if any(x in h.lower() for x in ['threshold', 'low', 'min', 'limit', 'quantity'])), None)

            if not name_col or not val_col:
                print(f"⚠️ Error: Could not match columns in {file_path}. Need 'Ingredient' and 'Threshold'.")
                return thresholds

            for row in reader:
                try:
                    name = row[name_col].strip()
                    val = float(row[val_col])
                    thresholds[name] = val
                except ValueError:
                    continue # Skip bad rows

            print(f"✅ Loaded {len(thresholds)} custom thresholds from {file_path}")
            return thresholds

    except Exception as e:
        print(f"❌ Error loading thresholds: {e}")
        return {}

# Load the thresholds once at startup
INGREDIENT_THRESHOLDS = load_thresholds_from_csv(THRESHOLDS_CSV_PATH)

# --------------------------------------------------------------------------
# Helper Class: Inventory Manager
# --------------------------------------------------------------------------
class InventoryManager:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.inventory_levels = {}
        self.reload_inventory()

    def reload_inventory(self):
        if not os.path.exists(self.csv_path):
            print(f"⚠️ Warning: Inventory file {self.csv_path} not found.")
            return

        totals = {}
        try:
            with open(self.csv_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                # --- SMART COLUMN MAPPING ---
                headers = reader.fieldnames
                # Look for Name column (flexible check)
                name_col = next((h for h in headers if h.lower().replace(" ","").replace("_","") in ["ingredientname", "ingredient_name", "ingredientid", "name"]), None)
                # Look for Quantity column (flexible check)
                qty_col = next((h for h in headers if h.lower().replace(" ","").replace("_","") in ["currentquantity", "current_quantity", "quantity"]), None)
                # Look for Expiration column (flexible check)
                exp_col = next((h for h in headers if h.lower().replace(" ","").replace("_","") in ["expirationdate", "expiration_date", "expiry", "expdate"]), None)

                if not name_col or not qty_col:
                    print(f"❌ ERROR: Could not find Name/Quantity columns in {headers}")
                    return

                # Get today's date at midnight for comparison
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                for row in reader:
                    name = row[name_col].strip()

                    # --- SAFE SEARCH LOGIC ---
                    # Check if item is expired before adding to totals
                    if exp_col:
                        exp_str = row[exp_col].strip()
                        try:
                            # Parse date (Assuming MM/DD/YYYY format from your screenshots)
                            exp_date = datetime.strptime(exp_str, "%m/%d/%Y")

                            # If expiration date is strictly before today, it's spoiled.
                            if exp_date < today:
                                # Skip this row (do not add to total)
                                continue
                        except ValueError:
                            # If date is invalid or missing, we default to counting it
                            pass

                    try:
                        qty = float(row[qty_col])
                        totals[name] = totals.get(name, 0.0) + qty
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error loading inventory: {e}")

        self.inventory_levels = totals
        print(f"✅ Inventory Loaded. {len(self.inventory_levels)} ingredients tracked.")

    def get_quantity(self, ingredient_name: str) -> float:
        return self.inventory_levels.get(ingredient_name, 0.0)

    def get_threshold(self, ingredient_name: str) -> float:
        """Returns the specific threshold for an item, or the default."""
        return INGREDIENT_THRESHOLDS.get(ingredient_name, DEFAULT_LOW_THRESHOLD)

    def is_low(self, ingredient_name: str) -> bool:
        return self.get_quantity(ingredient_name) < self.get_threshold(ingredient_name)

    def is_out(self, ingredient_name: str) -> bool:
        return self.get_quantity(ingredient_name) <= 0

# --------------------------------------------------------------------------
# App Initialization
# --------------------------------------------------------------------------
app = FastAPI(
    title="Chef's Co-pilot API",
    description="Sprint 3: Smart Menu RAG + Owner Inventory Intel.",
    version="1.8.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Instances ---
inventory_manager = InventoryManager(INVENTORY_CSV_PATH)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
embedding_func = embedding_functions.DefaultEmbeddingFunction()

# Connect to Collections
try:
    menu_collection = chroma_client.get_collection(name="menu_items", embedding_function=embedding_func)
    inventory_collection = chroma_client.get_collection(name="inventory_items", embedding_function=embedding_func)
    print("✅ Connected to Menu & Inventory Collections.")
except Exception as e:
    print(f"⚠️ Error connecting to ChromaDB: {e}. Did you run ingest_data.py?")
    menu_collection = None
    inventory_collection = None

# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class PatronSearchRequest(BaseModel):
    query: str

class OwnerSearchRequest(BaseModel):
    query: str

class SubstitutionSuggestion(BaseModel):
    original_item: str
    suggested_item: str
    reason: str

class MenuItemResult(BaseModel):
    id: str
    name: str
    description: str
    price: float
    score: float
    substitution: Optional[SubstitutionSuggestion] = None
    availability_status: str

class InventorySearchResult(BaseModel):
    ingredient_name: str
    category: str
    current_quantity: float
    unit: str
    score: float
    status: str

class OwnerSearchResponse(BaseModel):
    results: List[InventorySearchResult]
    patron_results: List[MenuItemResult] = []

# --------------------------------------------------------------------------
# Logic: Patron Search (RAG 1)
# --------------------------------------------------------------------------
def find_menu_candidates(query: str, n_results=5) -> List[Dict]:
    if not menu_collection: return []
    results = menu_collection.query(query_texts=[query], n_results=n_results)
    if not results['ids']: return []

    parsed_results = []
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        subs_list = json.loads(meta.get("suggested_substitutions", "[]"))

        item = {
            "id": results['ids'][0][i],
            "name": meta.get("name"),
            "description": results['documents'][0][i],
            "price": meta.get("price"),
            "score": results['distances'][0][i],
            "suggested_substitutions": subs_list,
            "substitution": None,
            "availability_status": "In Stock"
        }
        parsed_results.append(item)
    return parsed_results

def check_stock_logic(item: Dict) -> Dict:
    subs_list = item.get("suggested_substitutions", [])

    # 1. Identify critical status
    trigger_status = "In Stock"
    active_trigger_name = None

    for sub in subs_list:
        trigger = sub.get("trigger_ingredient")
        if inventory_manager.is_out(trigger):
            trigger_status = "Out of Stock"
            active_trigger_name = trigger
            break # Critical failure takes precedence
        elif inventory_manager.is_low(trigger):
            trigger_status = "Low Stock"
            active_trigger_name = trigger

    # 2. If In Stock, return early
    if trigger_status == "In Stock":
        return item

    # 3. Try to Substitute
    for sub in subs_list:
        trigger = sub.get("trigger_ingredient")
        if trigger == active_trigger_name:
             # Create Suggestion
            reason_text = sub.get("rag_justification", "Better availability")

            suggestion = SubstitutionSuggestion(
                original_item=item['name'],
                suggested_item=f"{sub.get('suggest_item_name')}",
                reason=reason_text
            )
            item['substitution'] = suggestion
            item['availability_status'] = "Substituted"
            return item

    # 4. No Substitute Found? Apply the bad status.
    item['availability_status'] = trigger_status
    return item

def rank_results(items: List[Dict]) -> List[Dict]:
    def sort_key(item):
        status_priority = {
            "In Stock": 0,
            "Substituted": 1,
            "Low Stock": 2,
            "Out of Stock": 3
        }
        return (status_priority.get(item['availability_status'], 99), item['score'])
    return sorted(items, key=sort_key)

# --------------------------------------------------------------------------
# Logic: Owner Search (RAG 2)
# --------------------------------------------------------------------------
def find_inventory_candidates(query: str, n_results=5) -> List[InventorySearchResult]:
    if not inventory_collection: return []

    results = inventory_collection.query(query_texts=[query], n_results=n_results)
    if not results['ids']: return []

    candidates = []
    seen_ingredients = set()

    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        name = meta.get("ingredient_name")

        if name in seen_ingredients: continue
        seen_ingredients.add(name)

        qty = meta.get("current_quantity", 0.0)

        # Determine status using specific threshold
        threshold = inventory_manager.get_threshold(name)
        status = "High"
        if qty <= 0: status = "Out"
        elif qty < threshold: status = "Low"

        candidates.append(InventorySearchResult(
            ingredient_name=name,
            category=meta.get("category", "General"),
            current_quantity=qty,
            unit=meta.get("unit", "units"),
            score=results['distances'][0][i],
            status=status
        ))

    return candidates

# --------------------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------------------

@app.get("/api/v1/inventory", response_model=List[InventorySearchResult])
async def get_inventory():
    """Returns the full list of inventory items (for Zero State)."""
    if not inventory_collection: return []

    # Retrieve all items from the collection
    results = inventory_collection.get()

    output = []
    seen_ingredients = set()

    if results['ids']:
        for i in range(len(results['ids'])):
            meta = results['metadatas'][i]
            name = meta.get("ingredient_name")

            if name in seen_ingredients: continue
            seen_ingredients.add(name)

            qty = meta.get("current_quantity", 0.0)

            # Determine status using specific threshold
            threshold = inventory_manager.get_threshold(name)
            status = "High"
            if qty <= 0: status = "Out"
            elif qty < threshold: status = "Low"

            output.append(InventorySearchResult(
                ingredient_name=name,
                category=meta.get("category", "General"),
                current_quantity=qty,
                unit=meta.get("unit", "units"),
                score=1.0, # Default score for full list
                status=status
            ))

    return output

@app.post("/api/v1/patron_search", response_model=Dict[str, List[MenuItemResult]])
async def patron_search(request: PatronSearchRequest):
    print(f"🔎 Patron Query: {request.query}")
    candidates = find_menu_candidates(request.query)
    checked = [check_stock_logic(item) for item in candidates]

    # Filter out "Out of Stock" items
    available_candidates = [
        item for item in checked
        if item['availability_status'] != "Out of Stock"
    ]

    ranked = rank_results(available_candidates)

    output = []
    for item in ranked:
        output.append(MenuItemResult(
            id=item['id'],
            name=item['name'],
            description=item['description'],
            price=float(item['price']),
            score=item['score'],
            substitution=item.get('substitution'),
            availability_status=item['availability_status']
        ))
    return {"results": output}


@app.post("/api/v1/owner_substitute", response_model=OwnerSearchResponse)
async def owner_substitute(request: OwnerSearchRequest):
    print(f"👨‍🍳 Owner Query: {request.query}")
    inventory_results = find_inventory_candidates(request.query)
    return OwnerSearchResponse(
        results=inventory_results,
        patron_results=[]
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)