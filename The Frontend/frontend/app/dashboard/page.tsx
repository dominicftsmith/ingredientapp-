import InventoryDashboard from "../components/InventoryDashboard";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-50 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Chef's Co-Pilot: Owner View</h1>
        <InventoryDashboard />
      </div>
    </main>
  );
}