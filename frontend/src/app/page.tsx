"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Lock, Shield, Zap } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LandingPage() {
  const [username, setUsername] = useState("alice");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Ensure API Gateway is running on 8001
      const res = await fetch("http://localhost:8001/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        throw new Error("Invalid credentials");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-900/40 via-background to-background z-0" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />

      <div className="z-10 w-full max-w-6xl px-6 flex flex-col lg:flex-row items-center gap-16">
        
        {/* Left Side: Copy & Branding */}
        <motion.div 
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex-1 space-y-8"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-surface-border bg-surface/50 text-sm font-medium text-primary-100">
            <Shield className="w-4 h-4 text-primary-500" />
            <span>Bank-grade Security. Enterprise Scale.</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-tight">
            The Future of <br />
            <span className="text-gradient">Intelligent Banking.</span>
          </h1>
          
          <p className="text-lg text-gray-400 max-w-xl">
            Experience next-generation financial services powered by advanced AI. 
            Automate transactions, get instant insights, and manage your wealth with unprecedented clarity.
          </p>

          <div className="grid grid-cols-2 gap-6 pt-4">
            <div className="space-y-2">
              <Zap className="w-6 h-6 text-yellow-500" />
              <h3 className="font-semibold text-white">Instant Execution</h3>
              <p className="text-sm text-gray-500">Real-time processing across all banking nodes.</p>
            </div>
            <div className="space-y-2">
              <Lock className="w-6 h-6 text-green-500" />
              <h3 className="font-semibold text-white">Zero Trust Architecture</h3>
              <p className="text-sm text-gray-500">Every request cryptographically verified.</p>
            </div>
          </div>
        </motion.div>

        {/* Right Side: Login Form */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          className="w-full max-w-md"
        >
          <div className="glass-panel p-8 rounded-2xl shadow-2xl relative overflow-hidden group">
            {/* Subtle border glow effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            
            <div className="relative z-10">
              <div className="mb-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
                <p className="text-sm text-gray-400">Sign in to your NexusBank account</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-300">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-surface-border focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-all text-white placeholder-gray-600"
                    placeholder="Enter your username"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-300">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-black/50 border border-surface-border focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-all text-white placeholder-gray-600"
                    placeholder="••••••••"
                    required
                  />
                </div>

                {error && (
                  <motion.p 
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="text-red-400 text-sm text-center bg-red-500/10 py-2 rounded-lg"
                  >
                    {error}
                  </motion.p>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-white text-black font-semibold hover:bg-gray-200 focus:ring-4 focus:ring-white/20 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                >
                  {loading ? "Authenticating..." : "Access Portal"}
                  {!loading && <ArrowRight className="w-4 h-4" />}
                </button>
              </form>

              <div className="mt-6 text-center text-xs text-gray-500">
                <p>Default Accounts:</p>
                <p className="mt-1">Alice: <code>alice / password123</code></p>
                <p>Bob: <code>bob / password123</code></p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
