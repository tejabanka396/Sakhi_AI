import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Mic, Heart, MessageCircle, Volume2 } from 'lucide-react';
import { AnimatedCharacter } from '../components/avatar/AnimatedCharacter';

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col justify-between p-6 sm:p-10 relative overflow-hidden select-none">
      {/* Dynamic Background Lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[550px] h-[550px] bg-rose-500/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header */}
      <header className="flex items-center justify-between max-w-6xl mx-auto w-full z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-pink-500/20 to-purple-600/20 border border-pink-500/30 flex items-center justify-center p-1.5 shadow-[0_0_15px_rgba(236,72,153,0.3)]">
            <img src="/lotus_icon.png" alt="Sakhi AI Logo" className="w-7 h-7 object-contain" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-pink-400 via-purple-300 to-cyan-300 bg-clip-text text-transparent">
            Sakhi AI
          </span>
        </div>
      </header>

      {/* Hero Body */}
      <main className="flex-1 flex flex-col items-center justify-center text-center my-8 z-10 max-w-4xl mx-auto w-full">
        {/* Center Animated Character with Floating Badges */}
        <div className="relative mb-6">
          <AnimatedCharacter gender="female" friendName="Sakhi" size="xl" />

          {/* Floating badge 1: Telugu snippet */}
          <div className="absolute -top-4 -left-12 sm:-left-20 bg-slate-900/90 border border-slate-700/80 px-3.5 py-1.5 rounded-2xl shadow-xl flex items-center gap-2 animate-bounce [animation-duration:3.5s]">
            <span className="text-xs font-semibold text-rose-300">"ఎలా ఉన్నావు?"</span>
            <span className="text-[11px] text-slate-400">Telugu AI</span>
          </div>

          {/* Floating badge 2: Listening wave */}
          <div className="absolute top-1/2 -right-12 sm:-right-24 bg-slate-900/90 border border-purple-500/40 px-3.5 py-1.5 rounded-2xl shadow-xl flex items-center gap-2 animate-bounce [animation-duration:4.2s]">
            <Volume2 className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-xs font-medium text-slate-200">Natural Voice</span>
          </div>

          {/* Floating badge 3: Warm Heart */}
          <div className="absolute -bottom-2 -left-6 sm:-left-12 bg-slate-900/90 border border-rose-500/40 px-3 py-1.5 rounded-2xl shadow-xl flex items-center gap-1.5 animate-bounce [animation-duration:3.8s]">
            <Heart className="w-3.5 h-3.5 text-rose-500 fill-current" />
            <span className="text-xs font-medium text-slate-200">AI Friend</span>
          </div>
        </div>

        {/* Heading & Subheading */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-3xl leading-[1.15] mb-4">
          Meet <span className="bg-gradient-to-r from-rose-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">Sakhi AI</span>
        </h1>
        <p className="text-lg sm:text-xl text-slate-300 max-w-xl font-normal leading-relaxed mb-8">
          Your AI friend who listens, talks and stays with you in natural Telugu and English.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
          <button
            onClick={() => navigate('/register')}
            className="w-full sm:w-auto px-9 py-4 rounded-2xl bg-gradient-to-r from-rose-500 via-pink-500 to-purple-600 hover:scale-105 text-white font-bold text-lg shadow-2xl shadow-rose-950/60 transition-all flex items-center justify-center gap-2.5 animate-pulseGlow"
          >
            <Sparkles className="w-5 h-5" />
            <span>Get Started Free</span>
          </button>
          <button
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-slate-200 font-semibold text-lg transition-all"
          >
            Login to Sakhi
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-slate-400 text-xs py-4 border-t border-slate-900 z-10">
        <p>Talk. Laugh. Learn. With Sakhi AI. ❤️ Designed for Telugu & English Voice Conversations.</p>
      </footer>
    </div>
  );
};
