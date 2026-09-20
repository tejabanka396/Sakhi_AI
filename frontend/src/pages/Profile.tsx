import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Settings, User as UserIcon, Heart, Sparkles, LogOut, Shield, Volume2, Globe, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getVoiceLabel } from '../services/voice';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, friendProfile, settings, logout } = useAuth();
  const { success } = useToast();

  const friendName = friendProfile?.friend_name || (friendProfile?.gender === 'male' ? 'Sakha' : 'Sakhi');
  const gender = friendProfile?.gender || 'female';
  const personality = friendProfile?.personality || 'friendly';
  const alwaysSpeak = settings?.always_speak ?? true;
  const langPref = settings?.language_preference || 'auto';

  const handleLogout = async () => {
    await logout();
    success('Logged out successfully. See you soon! ❤️');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[#070B14] text-white p-4 sm:p-8 select-none relative overflow-hidden">
      {/* Background atmospheric glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-purple-900/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-10 right-10 w-[450px] h-[450px] bg-pink-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[130px] pointer-events-none" />

      <div className="max-w-2xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/home')}
            aria-label="Back to Home"
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all flex items-center gap-2 text-sm font-medium shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Home</span>
          </button>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>User Profile</span>
          </h1>
          <button
            onClick={() => navigate('/settings')}
            aria-label="Open Settings"
            className="p-2.5 rounded-xl bg-purple-950/60 hover:bg-purple-900/80 border border-purple-500/30 text-purple-200 hover:text-white transition-all flex items-center gap-1.5 text-xs font-semibold shadow-md"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Settings</span>
          </button>
        </div>

        {/* User Card */}
        <div className="bg-slate-900/80 border border-white/10 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl mb-6">
          <div className="flex items-center gap-4 sm:gap-5">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center font-bold text-2xl sm:text-3xl text-white shadow-lg ring-2 ring-purple-400/30">
              {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-8 h-8" />}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl sm:text-2xl font-bold text-white truncate">
                {user?.name || 'Friend'}
              </h2>
              <p className="text-sm text-slate-400 truncate mt-0.5">
                {user?.email || 'No email attached'}
              </p>
              {user?.phone && (
                <p className="text-xs text-slate-500 truncate mt-0.5">
                  {user.phone}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Sakhi Companion Card */}
        <div className="bg-slate-900/80 border border-pink-500/20 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl mb-6">
          <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
            <div className="flex items-center gap-2.5">
              <Heart className="w-5 h-5 text-pink-400" />
              <h3 className="text-lg font-bold text-white">Your AI Companion</h3>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-300 font-medium">
              Active Friend
            </span>
          </div>

          <div className="flex items-center gap-4 mb-5">
            <div className="w-14 h-14 rounded-2xl overflow-hidden border border-pink-500/30 shrink-0 shadow-md">
              <img
                src={gender === 'male' ? '/characters/male_idle.jpg' : '/characters/female_idle.jpg'}
                alt={friendName}
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <h4 className="text-lg font-bold text-white">{friendName}</h4>
              <p className="text-xs text-slate-400 capitalize">
                {gender} Companion • {personality}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-2xl bg-slate-950/60 border border-white/5 flex items-center gap-3">
              <Volume2 className="w-4 h-4 text-purple-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[11px]">Voice Profile</span>
                <span className="text-white font-medium text-xs">{getVoiceLabel(gender)}</span>
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-slate-950/60 border border-white/5 flex items-center gap-3">
              <Globe className="w-4 h-4 text-cyan-400 shrink-0" />
              <div>
                <span className="text-slate-400 block text-[11px]">Language Preference</span>
                <span className="text-white font-medium capitalize">{langPref}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions (Dedicated Profile -> Settings flow) */}
        <div className="space-y-3">
          <button
            onClick={() => navigate('/settings')}
            className="w-full p-4 rounded-2xl bg-gradient-to-r from-purple-900/50 via-slate-900/90 to-pink-900/40 hover:from-purple-900/70 hover:to-pink-900/60 border border-purple-500/30 flex items-center justify-between text-left transition-all shadow-lg group"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300">
                <Settings className="w-5 h-5 group-hover:rotate-45 transition-transform duration-300" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Customize Sakhi & App Settings</h4>
                <p className="text-xs text-slate-400">Change voice, dialect style, names, and modes</p>
              </div>
            </div>
            <span className="text-xs font-semibold text-pink-400 group-hover:translate-x-1 transition-transform">
              Open &rarr;
            </span>
          </button>

          <button
            onClick={handleLogout}
            className="w-full p-4 rounded-2xl bg-slate-900/60 hover:bg-red-950/30 border border-white/10 hover:border-red-500/30 flex items-center justify-between text-left transition-all text-slate-300 hover:text-red-300"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400">
                <LogOut className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Sign Out</h4>
                <p className="text-xs text-slate-500">Log out of this device</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
