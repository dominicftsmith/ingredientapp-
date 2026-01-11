export interface Substitution {
  trigger_ingredient: string;
  suggest_item_name: string;
  price: number;
  rag_justification: string;
  is_inventory_optimization: boolean; // True if suggested because original stock is low
}

export interface MenuItem {
  id: string;
  name: string;
  description: string;
  base_price: number;        // A La Carte Price
  meal_price?: number | null; // Optional: Bundle Price
  category: string;
  image_url?: string;        // Placeholder for demo
  substitution?: Substitution | null; // The "Smart Intel" payload
}