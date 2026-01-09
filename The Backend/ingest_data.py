import json
import csv
import chromadb
from chromadb.utils import embedding_functions
import os

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
DATA_PATH_MENU = "menu.json"
DATA_PATH_INVENTORY = "inventory_lots.csv"
CHROMA_DB_PATH = "./chroma_db"

# Initialize ChromaDB Client (Persistent)
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
embedding_func = embedding_functions.DefaultEmbeddingFunction()

# --------------------------------------------------------------------------
# 1. Ingest Menu (JSON)
# --------------------------------------------------------------------------
def ingest_menu():
    print(f"--- Ingesting Menu from {DATA_PATH_MENU} ---")
    
    # Robust cleanup: Try to delete, but ignore errors if it doesn't exist
    try:
        client.delete_collection(name="menu_items")
    except Exception:
        pass 
    
    # Create the collection fresh
    collection = client.create_collection(
        name="menu_items",
        embedding_function=embedding_func
    )

    if not os.path.exists(DATA_PATH_MENU):
        print(f"❌ ERROR: {DATA_PATH_MENU} not found in {os.getcwd()}")
        return

    with open(DATA_PATH_MENU, 'r') as f:
        data = json.load(f)

    documents = []
    metadatas = []
    ids = []

    # Helper to process items
    def process_item(item):
        doc_text = f"{item['name']}. {item['description']}. Tags: {', '.join(item.get('tags', []))}"
        documents.append(doc_text)
        ids.append(item['id'])
        metadatas.append({
            "name": item['name'],
            "category": item['category'],
            "price": item['price'],
            "suggested_substitutions": json.dumps(item.get('suggested_substitutions', []))
        })

    # Loop through categories
    for category, items in data['menu'].items():
        for item in items:
            process_item(item)

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"✅ Successfully added {len(documents)} menu items.")

# --------------------------------------------------------------------------
# 2. Ingest Inventory (CSV)
# --------------------------------------------------------------------------
def ingest_inventory():
    print(f"\n--- Ingesting Inventory from {DATA_PATH_INVENTORY} ---")
    
    try:
        client.delete_collection(name="inventory_items")
    except Exception:
        pass
    
    collection = client.create_collection(
        name="inventory_items",
        embedding_function=embedding_func
    )

    if not os.path.exists(DATA_PATH_INVENTORY):
        print(f"❌ ERROR: Inventory CSV not found in {os.getcwd()}")
        return

    documents = []
    metadatas = []
    ids = []

    with open(DATA_PATH_INVENTORY, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_text = f"{row['IngredientName']}. Category: {row['Category']}."
            documents.append(doc_text)
            ids.append(row['LotID'])
            metadatas.append({
                "IngredientName": row['IngredientName'],
                "Category": row['Category'],
                "CurrentQuantity": float(row['CurrentQuantity']),
                "DefaultUnit": row['DefaultUnit'],
                "ExpirationDate": row['ExpirationDate']
            })

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"✅ Successfully added {len(documents)} inventory lots.")

# --------------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------------
if __name__ == "__main__":
    ingest_menu()
    ingest_inventory()
    print("\n🎉 Ingestion Complete! Database is ready.")