"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, LayoutDashboard, CreditCard, Receipt, Settings, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
      return;
    }

    // Fetch user profile
    fetch("http://localhost:8001/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then(data => setUser(data))
      .catch(() => {
        localStorage.removeItem("token");
        router.push("/");
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center bg-black"><div className="animate-pulse text-white">Loading Nexus...</div></div>;
  }

  const navItems = [
    { name: "Overview", icon: LayoutDashboard, active: true },
    { name: "Cards", icon: CreditCard, active: false },
    { name: "Transactions", icon: Receipt, active: false },
    { name: "Settings", icon: Settings, active: false },
  ];

  return (
    <div className="min-h-screen bg-black flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-surface-border bg-surface flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-surface-border">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-500 to-purple-500">
            NexusBank
          </h1>
        </div>
        
        <div className="flex-1 py-6 px-4 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.name}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm font-medium",
                item.active 
                  ? "bg-primary-500/10 text-primary-500" 
                  : "text-gray-400 hover:bg-surface-hover hover:text-white"
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-surface-border">
          <div className="flex items-center gap-3 px-4 py-3 bg-surface-hover rounded-xl mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center text-white font-bold">
              {user.full_name.charAt(0)}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {children}
      </main>
    </div>
  );
}
