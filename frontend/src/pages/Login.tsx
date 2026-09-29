import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Lock, User, ArrowRight } from 'lucide-react';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('officer_1');
  const [password, setPassword] = useState('bhusetu');
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Default prototype session login
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 space-y-6">
        <div className="text-center">
          <div className="w-12 h-12 bg-emerald-700 text-white rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">BhuSetu Portal</h2>
          <p className="text-xs text-slate-500 mt-1">
            Department of Land Resources • Ministry of Rural Development
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">Officer Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 font-medium"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">Secure Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 font-medium"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-sm shadow flex items-center justify-center gap-2 transition-colors"
          >
            <span>Authenticate Session</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t border-slate-100 text-center text-[11px] text-slate-500 space-y-1">
          <p>Demo Roles Available:</p>
          <div className="flex justify-center gap-2 font-mono text-[10px]">
            <span
              onClick={() => { setUsername('officer_1'); setPassword('bhusetu'); }}
              className="bg-slate-100 px-2 py-0.5 rounded cursor-pointer hover:bg-emerald-100"
            >
              officer_1
            </span>
            <span
              onClick={() => { setUsername('admin'); setPassword('admin123'); }}
              className="bg-slate-100 px-2 py-0.5 rounded cursor-pointer hover:bg-emerald-100"
            >
              admin
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
