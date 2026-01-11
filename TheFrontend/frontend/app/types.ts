export interface Substitution {
  trigger_ingredient: string;
  suggest_item_id: string;
  suggest_item_name: string;
  rag_justification: string;
}

export interface MenuItem {
  id: string;
  name: string; // Confirmed: API uses "name", not "item_name"
  description: string;
  price: number;
  category: string;
  type: string; // e.g., "Meal"
  tags: string[];
  suggested_substitutions: Substitution[]; // Confirmed: API returns an array
}

// NEW: Owner-Facing Inventory Type
export interface InventoryItem {
  id: string;
  ingredient_name: string;
  total_on_hand: number;
  unit: string;
  safety_threshold: number;
}