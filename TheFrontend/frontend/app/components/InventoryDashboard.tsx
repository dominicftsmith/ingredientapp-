"use client";

import { InventoryItem } from "../types";

// MOCK DATA: Simulating the inventory.db query you described
const MOCK_INVENTORY: InventoryItem[] = [
  { id: "INV-001", ingredient_name: "Ground Beef", total_on_hand: 8.0, unit: "lbs", safety_threshold: 10.0 }, // LOW
  { id: "INV-002", ingredient_name: "Chicken Breast", total_on_hand: 25.0, unit: "lbs", safety_threshold: 15.0 }, // OK
  { id: "INV-003", ingredient_name: "Potatoes", total_on_hand: 4.5, unit: "lbs", safety_threshold: 20.0 }, // CRITICAL
  { id: "INV-004", ingredient_name: "Lettuce", total_on_hand: 12.0, unit: "heads", safety_threshold: 5.0 }, // OK
];

export default function InventoryDashboard() {
  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-slate-200">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Inventory Intel</h2>
        <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-sm font-medium">
          Live Connection: Syncing...
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-slate-500 border-b border-slate-100 text-sm uppercase tracking-wider">
              <th className="p-4 font-semibold">Ingredient</th>
              <th className="p-4 font-semibold">On Hand</th>
              <th className="p-4 font-semibold">Threshold</th>
              <th className="p-4 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {MOCK_INVENTORY.map((item) => {
              // LOGIC: Total On Hand < Safety Threshold
              const isLowStock = item.total_on_hand < item.safety_threshold;
              
              return (
                <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-4 font-medium text-slate-900">{item.ingredient_name}</td>
                  <td className="p-4 text-slate-700">
                    {item.total_on_hand} <span className="text-slate-400 text-sm">{item.unit}</span>
                  </td>
                  <td className="p-4 text-slate-400">
                    {item.safety_threshold} {item.unit}
                  </td>
                  <td className="p-4">
                    {isLowStock ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        LOW STOCK
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                        OK
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}