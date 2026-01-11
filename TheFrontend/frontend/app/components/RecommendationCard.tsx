"use client";

import { MenuItem } from "../types";

export default function RecommendationCard({ item }: { item: MenuItem }) {
  // 1. Check if this item is a "Smart Suggestion"
  // Logic: If the 'suggested_substitutions' array has items, it's a suggestion.
  const isSuggestion = item.suggested_substitutions && item.suggested_substitutions.length > 0;
  
  // 2. Get the justification from the first suggestion (if it exists)
  const justification = isSuggestion ? item.suggested_substitutions[0].rag_justification : null;

  return (
    <div className={`relative flex flex-col justify-between p-6 border rounded-xl shadow-sm transition-all hover:shadow-md ${isSuggestion ? "border-amber-400 bg-amber-50" : "border-slate-200 bg-white"}`}>
      
      {/* BADGE: Chef's Suggestion */}
      {isSuggestion && (
        <div className="absolute -top-3 left-4 bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
          Chef's Suggestion
        </div>
      )}

      <div>
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-bold text-slate-800">{item.name}</h3>
          <span className="text-xl font-semibold text-emerald-600">
            ${item.price.toFixed(2)}
          </span>
        </div>

        <p className="text-slate-600 text-sm mb-4 leading-relaxed">
          {item.description}
        </p>

        {/* JUSTIFICATION: Why was this suggested? */}
        {justification && (
           <div className="mb-4 p-3 bg-white/60 border border-amber-200 rounded-lg text-sm text-slate-700 italic">
             <span className="font-semibold not-italic text-amber-600">💡 Why this? </span> 
             "{justification}"
           </div>
        )}
      </div>
      
      {/* Note: "Meal Toggle" removed because the current API only returns a single fixed price. */}
    </div>
  );
}