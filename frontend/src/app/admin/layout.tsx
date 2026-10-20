"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, Shield, Database, Users, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiFetch, logout } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    apiFetch("/api/v1/auth/me")
      .then(res => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then(data => {
        setUser(data);
        return apiFetch("/api/v1/auth/me/roles");
      })
      .then(res => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((roles: string[]) => {
        if (!roles.includes("ADMIN")) {
           router.push("/dashboard");
        }
      })
      .catch(() => router.push("/"));
  }, [router]);

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center bg-black"><div className="animate-pulse text-white">Loading Nexus Admin...</div></div>;
  }

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    user?.email ||
    "User";

  const avatarLetter = displayName.charAt(0).toUpperCase();

  const navItems = [
    { name: "Knowledge Base", icon: Database, active: true },
    { name: "Users", icon: Users, active: false },
    { name: "Security", icon: Shield, active: false },
    { name: "Settings", icon: Settings, active: false },
  ];

  return (
    <div className="min-h-screen bg-black flex overflow-hidden">
      <aside className="w-64 border-r border-surface-border bg-surface flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-surface-border">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-orange-500">
            Nexus Admin
          </h1>
        </div>
        
        <div className="flex-1 py-6 px-4 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.name}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm font-medium",
                item.active 
                  ? "bg-red-500/10 text-red-500" 
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
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center text-white font-bold">
              {avatarLetter}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-white truncate">{displayName}</p>
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

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {children}
      </main>
    </div>
  );
}
