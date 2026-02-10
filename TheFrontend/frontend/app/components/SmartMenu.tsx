"use client";

import { useState } from "react";
import { MenuItem } from "../types";
import RecommendationCard from "./RecommendationCard";

export default function SmartMenu() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MenuItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // We are hardcoding the live server for the demo
const API_BASE_URL = "https://chef-demo-backend.onrender.com";

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResults([]); 

    try {
      console.log(`Sending request to: ${API_BASE_URL}/api/v1/patron_search`);
      
      // CHANGE 2: Updated path to match your api.py (@app.post("/api/v1/patron_search"))
      const response = await fetch(`${API_BASE_URL}/api/v1/patron_search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query }), 
      });

      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }

      const rawData = await response.json();
      console.log("DEBUG - Backend Response:", rawData); 

      let items: MenuItem[] = [];

      // Logic to handle different response structures
      if (Array.isArray(rawData)) {
        items = rawData;
      } 
      else if (rawData.results && Array.isArray(rawData.results)) {
        items = rawData.results;
      }
      else if (rawData.data && Array.isArray(rawData.data)) {
        items = rawData.data;
      } 
      else {
        // If it's a single object, wrap it
        if (typeof rawData === 'object') {
           items = [rawData as unknown as MenuItem];
        }
      }

      setResults(items);
      setHasSearched(true);

    } catch (err) {
      console.error(err);
      setError("Connection failed. If this is the first search in a while, the free demo server might be waking up. Please try again in 30 seconds.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="max-w-4xl mx-auto p-4">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          What are you craving?
        </h2>
        <p className="text-slate-500 mt-2">
          Powered by AI. Connected to Live Inventory.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative max-w-xl mx-auto mb-12">
        <input
          type="text"
          placeholder="e.g., 'I want a burger...'"
          className="w-full p-4 pl-6 pr-14 rounded-full border-2 border-slate-200 shadow-sm focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all text-lg placeholder-slate-400 text-slate-900"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button 
          type="submit"
          className="absolute right-2 top-2 bottom-2 bg-emerald-600 text-white px-6 rounded-full font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "..." : "Ask"}
        </button>
      </form>

      {/* CHANGE 3: Better Error/Loading State for Free Tier */}
      {loading && (
          <div className="text-center text-sm text-slate-400 mb-6 animate-pulse">
            Thinking... (Note: Free demo servers may take 30s to wake up on first use)
          </div>
      )}

      {error && <div className="text-center text-red-500 mb-6 text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {hasSearched && results.length > 0 ? (
          results.map((item, index) => (
            <RecommendationCard key={item.id || index} item={item} />
          ))
        ) : (
           hasSearched && !loading && (
             <p className="col-span-2 text-center text-slate-400">
               No items found. Try asking for "burger" or "salad".
             </p>
           )
        )}
      </div>
    </section>
  );
}