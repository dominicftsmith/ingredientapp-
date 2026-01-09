import sqlite3
import pandas as pd
import os

# Configuration: Update these filenames to match your local files
FILES = {
    'vendors': 'vendors.csv',           # Found extra col: VendorCode
    'ingredients': 'ingredients.csv',   
    'inventory': 'inventory_lots.csv',  # Found extra col: IngredientName (will be ignored)
    'recipes': 'dish.csv'               # Mapped manually below
}

DB_NAME = 'inventory.db'

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to DB: {e}")
    return None

def create_schema(conn):
    cursor = conn.cursor()
    
    # 1. Vendors Table (Includes VendorCode now)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vendors (
        VendorID TEXT PRIMARY KEY,
        VendorName TEXT,
        ContactEmail TEXT,
        VendorCode TEXT
    );""")

    # 2. Ingredients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ingredients (
        IngredientID TEXT PRIMARY KEY,
        IngredientName TEXT,
        Category TEXT,
        DefaultUnit TEXT,
        LowThreshold REAL,
        HighThreshold REAL
    );""")

    # 3. Inventory Lots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Inventory_Lots (
        LotID TEXT PRIMARY KEY,
        IngredientID TEXT,
        VendorID TEXT,
        PurchaseDate TEXT,
        ExpirationDate TEXT,
        PurchaseQuantity REAL,
        CurrentQuantity REAL,
        FOREIGN KEY (IngredientID) REFERENCES Ingredients (IngredientID)
    );""")

    # 4. Recipe Components Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Recipe_Components (
        ComponentID TEXT,
        ParentItemID TEXT,
        ChildItemID TEXT,
        Quantity REAL,
        Unit TEXT,
        SubAssemblyReference TEXT
    );""")
    
    print("Schema created.")

def import_csv_to_table(conn, csv_path, table_name, column_map=None):
    """
    Smart Import: Only imports columns that actually exist in the target SQL table.
    """
    if not os.path.exists(csv_path):
        print(f"Warning: File {csv_path} not found. Skipping table {table_name}.")
        return

    try:
        df = pd.read_csv(csv_path)
        
        # 1. Apply column mapping if provided
        if column_map:
            df = df.rename(columns=column_map)
        
        # 2. ASK THE DATABASE: What columns do you have?
        cursor = conn.cursor()
        # Get list of columns from the actual table
        # PRAGMA table_info returns tuples: (cid, name, type, notnull, dflt_value, pk)
        table_info = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        
        # Extract column names (index 1 in the tuple)
        valid_db_columns = [row[1] for row in table_info]
        
        # 3. FILTER THE CSV: Keep only columns that match the database
        # Find intersection of CSV columns and DB columns
        cols_to_keep = [col for col in df.columns if col in valid_db_columns]
        
        if not cols_to_keep:
            print(f"CRITICAL: No matching columns found for {table_name}. Skipping.")
            return

        # Create a clean dataframe with ONLY the valid columns
        df_clean = df[cols_to_keep]

        # 4. Insert
        df_clean.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Successfully imported {len(df_clean)} rows into {table_name} from {csv_path} (Cols kept: {cols_to_keep})")
        
    except Exception as e:
        print(f"Error importing {csv_path} into {table_name}: {e}")

def main():
    # NUCLEAR OPTION: Remove old DB to ensure clean build from CSVs
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(f"Removed old {DB_NAME} for fresh build.")
        except PermissionError:
            print(f"ERROR: Could not delete {DB_NAME}. Is it open in another program (like DB Browser or the running API)?")
            print("Please close any programs using the database and try again.")
            return

    conn = create_connection(DB_NAME)
    
    if conn:
        create_schema(conn)
        
        # 1. Import Vendors
        import_csv_to_table(conn, FILES['vendors'], 'Vendors')
        
        # 2. Import Ingredients
        import_csv_to_table(conn, FILES['ingredients'], 'Ingredients')
        
        # 3. Import Inventory Lots (This will now safely ignore 'IngredientName')
        import_csv_to_table(conn, FILES['inventory'], 'Inventory_Lots')
        
        # 4. Import Recipes (dish.csv) with Mapping
        dish_map = {
            'MenuItemID': 'ParentItemID',
            'ComponentID': 'ChildItemID',
            'Quantity': 'Quantity',
            'Unit': 'Unit',
            'PartofItemID': 'SubAssemblyReference'
        }
        import_csv_to_table(conn, FILES['recipes'], 'Recipe_Components', column_map=dish_map)
        
        conn.close()
        print(f"\nDatabase {DB_NAME} build complete.")
    else:
        print("Failed to create database connection.")

if __name__ == '__main__':
    main()