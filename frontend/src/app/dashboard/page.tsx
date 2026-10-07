"use client";

import { useEffect, useState, useRef } from "react";
import { Send, CreditCard, Wallet, TrendingUp, Sparkles, User, Bot, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { v4 as uuidv4 } from "uuid";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolResult?: any;
}

export default function Dashboard() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  
  const [messages, setMessages] = useState<Message[]>([
    { id: "msg-0", role: "assistant", content: "Hello! I'm your Nexus AI Assistant. How can I help you manage your finances today?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const conversationId = useRef(uuidv4());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const fetchAccounts = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8001/api/v1/accounts", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAccounts(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAccounts(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    
    setMessages(prev => [...prev, { id: uuidv4(), role: "user", content: userMessage }]);
    setIsTyping(true);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8001/api/v1/chat", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId.current,
        }),
      });
      
      const data = await res.json();
      
      setMessages(prev => [...prev, { 
        id: uuidv4(), 
        role: "assistant", 
        content: data.response_message || "Done.",
        toolResult: data.tool_result 
      }]);

      // Refresh accounts in case the agent did something
      fetchAccounts();
    } catch (e) {
      setMessages(prev => [...prev, { 
        id: uuidv4(), 
        role: "assistant", 
        content: "I'm having trouble connecting to the banking core right now." 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden p-6 gap-6">
      
      {/* Left Column: Accounts & Stats */}
      <div className="w-full lg:w-1/3 flex flex-col gap-6 overflow-y-auto pr-2 pb-6">
        <div>
          <h2 className="text-2xl font-semibold text-white mb-6">Financial Overview</h2>
          
          <div className="grid gap-4">
            {loadingAccounts ? (
              <div className="h-32 glass-panel rounded-2xl animate-pulse flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
              </div>
            ) : accounts.length === 0 ? (
              <div className="h-32 glass-panel rounded-2xl flex flex-col items-center justify-center text-gray-400">
                <Wallet className="w-8 h-8 mb-2 opacity-50" />
                <p>No accounts found</p>
              </div>
            ) : (
              accounts.map((acc, i) => (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  key={acc.id} 
                  className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
                >
                  <div className="absolute -right-10 -top-10 w-32 h-32 bg-primary-500/10 rounded-full blur-2xl group-hover:bg-primary-500/20 transition-all" />
                  
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <p className="text-sm text-gray-400 mb-1">{acc.account_type.replace("_", " ").toUpperCase()}</p>
                      <p className="text-xs font-mono text-gray-500">{acc.account_number}</p>
                    </div>
                    <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                      <Wallet className="w-4 h-4 text-primary-400" />
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-3xl font-bold text-white tracking-tight">
                      {acc.currency} {parseFloat(acc.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="glass-panel p-4 rounded-xl flex items-center gap-3 cursor-pointer hover:bg-white/5 transition-colors">
            <div className="p-2 bg-green-500/10 rounded-lg text-green-400"><TrendingUp className="w-4 h-4" /></div>
            <div>
              <p className="text-sm font-medium text-white">Invest</p>
              <p className="text-xs text-gray-500">View options</p>
            </div>
          </div>
          <div className="glass-panel p-4 rounded-xl flex items-center gap-3 cursor-pointer hover:bg-white/5 transition-colors">
            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400"><CreditCard className="w-4 h-4" /></div>
            <div>
              <p className="text-sm font-medium text-white">Cards</p>
              <p className="text-xs text-gray-500">Manage</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: AI Chat */}
      <div className="w-full lg:w-2/3 h-full flex flex-col bg-surface/50 rounded-3xl border border-surface-border overflow-hidden relative shadow-2xl">
        <div className="h-16 border-b border-surface-border flex items-center px-6 bg-surface z-10 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 p-0.5">
              <div className="w-full h-full bg-black rounded-full flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Nexus Assistant</h2>
              <p className="text-xs text-green-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 block" /> Online
              </p>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={msg.id} 
              className={`flex gap-4 max-w-[85%] ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
            >
              <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                msg.role === "user" ? "bg-surface-hover border border-surface-border" : "bg-primary-500/20 text-primary-400"
              }`}>
                {msg.role === "user" ? <User className="w-4 h-4 text-gray-400" /> : <Bot className="w-4 h-4" />}
              </div>
              
              <div className={`space-y-2 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className={`px-5 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user" 
                    ? "bg-white text-black rounded-tr-sm" 
                    : "bg-surface border border-surface-border text-gray-200 rounded-tl-sm"
                }`}>
                  {msg.content}
                </div>
                
                {msg.toolResult && (
                  <div className="bg-black/40 border border-surface-border p-3 rounded-xl text-xs font-mono text-gray-400 overflow-x-auto max-w-full">
                    <pre>{JSON.stringify(msg.toolResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          
          {isTyping && (
            <div className="flex gap-4 max-w-[85%]">
              <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div className="px-5 py-4 rounded-2xl bg-surface border border-surface-border rounded-tl-sm flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-surface border-t border-surface-border">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me to transfer money, block a card, or show your balance..."
              className="w-full bg-black/50 border border-surface-border text-white text-sm rounded-xl px-4 py-4 pr-12 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-all placeholder-gray-600"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 p-2 bg-white text-black rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:hover:bg-white transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-[10px] text-gray-600 uppercase tracking-wider font-medium">NexusBank AI Assistant can make mistakes. Consider verifying important information.</p>
          </div>
        </div>
      </div>
      
    </div>
  );
}
