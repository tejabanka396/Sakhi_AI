import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, User, MessageSquare, LogOut,
  Trash2, Volume2, Square, Sparkles, Loader2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useVoice } from '../context/VoiceContext';
import { getVoiceForGender, getVoiceLabel, getVoiceDescription } from '../services/voice';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Gender, ConversationMode, LanguagePreference } from '../types';

export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    user, friendProfile, settings, logout,
    updateUser, updateFriendProfile, updateSettings, deleteAccount
  } = useAuth();
  const { success, error: toastError } = useToast();

  // Profile Form state
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [phone, setPhone] = useState(user?.phone || '');

  // Sakhi customization state
  const [friendName, setFriendName] = useState(friendProfile?.friend_name || 'Sakhi');
  const [gender, setGender] = useState<Gender>(friendProfile?.gender || 'female');
  const [personality, setPersonality] = useState(friendProfile?.personality || 'friendly');

  // Conversation Settings state
  const [defaultMode, setDefaultMode] = useState<ConversationMode>(settings?.default_mode || 'talk');
  const [alwaysSpeak, setAlwaysSpeak] = useState<boolean>(settings?.always_speak || false);
  const [langPref, setLangPref] = useState<LanguagePreference>(settings?.language_preference || 'auto');

  const { previewVoice, stopSpeaking, isSpeaking } = useVoice();

  // Voice preview state
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null);
  const [loadingVoice, setLoadingVoice] = useState<string | null>(null);

  // Modals state
  const [isLogoutOpen, setIsLogoutOpen] = useState(false);
  const [isDeleteAccountOpen, setIsDeleteAccountOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  useEffect(() => {
    if (!isSpeaking) {
      setPreviewingVoice(null);
    }
  }, [isSpeaking]);

  useEffect(() => {
    if (friendProfile) {
      if (friendProfile.friend_name) setFriendName(friendProfile.friend_name);
      if (friendProfile.gender) setGender(friendProfile.gender);
      if (friendProfile.personality) setPersonality(friendProfile.personality);
    }
  }, [friendProfile]);

  const currentVoiceId = getVoiceForGender(gender);
  const isCurrentPreviewPlaying = previewingVoice === currentVoiceId;
  const isCurrentPreviewLoading = loadingVoice === currentVoiceId;

  const handlePlayPreview = async (vId: string) => {
    if (previewingVoice === vId) {
      stopSpeaking();
      setPreviewingVoice(null);
      return;
    }

    try {
      setLoadingVoice(vId);
      setPreviewingVoice(vId);
      await previewVoice(vId);
    } catch {
      toastError('Voice preview unavailable.');
      setPreviewingVoice(null);
    } finally {
      setLoadingVoice(null);
    }
  };

  const handleGenderChange = (newGender: Gender) => {
    setGender(newGender);
    if (friendName === 'Sakhi' && newGender === 'male') {
      setFriendName('Sakha');
    } else if (friendName === 'Sakha' && newGender === 'female') {
      setFriendName('Sakhi');
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateUser({ name, email, phone: phone || undefined });
      success('Profile updated ✓');
    } catch {
      toastError('Could not update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSakhiCustomization = async () => {
    setIsSaving(true);
    try {
      const targetVoiceId = getVoiceForGender(gender);
      await updateFriendProfile({
        friend_name: friendName.trim() || (gender === 'female' ? 'Sakhi' : 'Sakha'),
        gender,
        voice_id: targetVoiceId,
        personality,
      });
      success('Sakhi settings updated ✓');
    } catch {
      toastError('Could not update Sakhi settings.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleAlwaysSpeak = async () => {
    const newVal = !alwaysSpeak;
    setAlwaysSpeak(newVal);
    await updateSettings({ always_speak: newVal });
    success(`Always speak responses: ${newVal ? 'ON' : 'OFF'}`);
  };

  const handleModeChange = async (mode: ConversationMode) => {
    setDefaultMode(mode);
    await updateSettings({ default_mode: mode });
    success(`Default mode set to ${mode.toUpperCase()} ✓`);
  };

  const handleLangChange = async (lang: LanguagePreference) => {
    setLangPref(lang);
    await updateSettings({ language_preference: lang });
    success(`Language preference set to ${lang} ✓`);
  };

  const handleLogout = async () => {
    await logout();
    success('Logged out successfully. See you soon! ❤️');
    navigate('/login');
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteAccount();
      success('Account deleted permanently.');
      navigate('/');
    } catch {
      toastError('Could not delete account.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-4 sm:p-8 select-none relative">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <button
            onClick={() => navigate('/home')}
            aria-label="Back to home"
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all flex items-center gap-2 text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Home</span>
          </button>
          <h1 className="text-xl font-bold tracking-tight text-white">Settings</h1>
          <div className="w-16" />
        </div>

        {/* 1. MY SAKHI CUSTOMIZATION */}
        <section className="bg-slate-900/80 border border-slate-800/80 p-6 rounded-3xl shadow-xl space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">My Sakhi</h2>
              <p className="text-xs text-slate-400">Personalize your AI companion</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Companion Name</label>
              <input
                type="text"
                value={friendName}
                onChange={(e) => setFriendName(e.target.value)}
                placeholder="Sakhi, Sakha, Anu, Lucky..."
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Character Gender</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleGenderChange('female')}
                  className={`py-2.5 px-3 rounded-xl text-xs font-semibold border transition-all ${
                    gender === 'female'
                      ? 'bg-rose-500/20 border-rose-500 text-rose-200 shadow-md ring-1 ring-rose-500/40'
                      : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-white'
                  }`}
                >
                  Female
                </button>
                <button
                  type="button"
                  onClick={() => handleGenderChange('male')}
                  className={`py-2.5 px-3 rounded-xl text-xs font-semibold border transition-all ${
                    gender === 'male'
                      ? 'bg-purple-500/20 border-purple-500 text-purple-200 shadow-md ring-1 ring-purple-500/40'
                      : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-white'
                  }`}
                >
                  Male
                </button>
              </div>
            </div>

            {/* Voice Section: Display Active Voice based on Companion Gender with Single Preview Button */}
            <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Voice</span>
                  <h3 className="text-sm font-bold text-white mt-0.5">{getVoiceLabel(gender)}</h3>
                </div>
                <button
                  type="button"
                  onClick={() => handlePlayPreview(currentVoiceId)}
                  className={`py-2 px-3.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    isCurrentPreviewPlaying
                      ? 'bg-gradient-to-r from-rose-500 to-purple-600 text-white shadow-lg animate-pulse'
                      : isCurrentPreviewLoading
                      ? 'bg-slate-700 text-rose-300'
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600'
                  }`}
                >
                  {isCurrentPreviewLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : isCurrentPreviewPlaying ? (
                    <Square className="w-3.5 h-3.5 fill-current" />
                  ) : (
                    <Volume2 className="w-3.5 h-3.5 text-rose-400" />
                  )}
                  <span>{isCurrentPreviewLoading ? 'Loading...' : isCurrentPreviewPlaying ? 'Stop' : 'Preview Voice'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Automatically selected based on your Sakhi character ({getVoiceDescription(gender)}).
              </p>
            </div>

            <button
              onClick={handleSaveSakhiCustomization}
              disabled={isSaving}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 hover:opacity-95 text-white font-semibold text-xs transition-all shadow-md"
            >
              {isSaving ? 'Saving...' : 'Save Sakhi Preferences'}
            </button>
          </div>
        </section>

        {/* 2. CONVERSATION PREFERENCES */}
        <section className="bg-slate-900/80 border border-slate-800/80 p-6 rounded-3xl shadow-xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Conversation & Mode</h2>
              <p className="text-xs text-slate-400">Interaction preferences</p>
            </div>
          </div>

          <div className="space-y-3 pt-1">
            {/* Talk / Chat / Auto */}
            <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-800/50 border border-slate-800">
              <div>
                <span className="text-sm font-semibold text-white block">Default Interaction Mode</span>
                <span className="text-xs text-slate-400">Choose voice-first or text-first</span>
              </div>
              <div className="flex gap-1 bg-slate-900 p-1 rounded-xl border border-slate-700/80">
                {(['talk', 'chat', 'auto'] as ConversationMode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => handleModeChange(m)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                      defaultMode === m
                        ? 'bg-rose-500 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Always Speak Switch */}
            <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-800/50 border border-slate-800">
              <div>
                <span className="text-sm font-semibold text-white block">Always Speak Responses</span>
                <span className="text-xs text-slate-400">Play spoken audio even when typing in Chat mode</span>
              </div>
              <button
                type="button"
                onClick={handleToggleAlwaysSpeak}
                className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                  alwaysSpeak ? 'bg-rose-500' : 'bg-slate-700'
                }`}
              >
                <div
                  className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                    alwaysSpeak ? 'translate-x-6' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Language Preference */}
            <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-800/50 border border-slate-800">
              <div>
                <span className="text-sm font-semibold text-white block">Language Preference</span>
                <span className="text-xs text-slate-400">Sakhi naturally adapts to Telugu, English, or mixed</span>
              </div>
              <select
                value={langPref}
                onChange={(e: any) => handleLangChange(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none"
              >
                <option value="auto">Auto Adapt</option>
                <option value="telugu">Telugu</option>
                <option value="english">English</option>
              </select>
            </div>
          </div>
        </section>

        {/* 3. PROFILE & ACCOUNT */}
        <section className="bg-slate-900/80 border border-slate-800/80 p-6 rounded-3xl shadow-xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Your Profile</h2>
              <p className="text-xs text-slate-400">Manage account information</p>
            </div>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Your Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Phone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91..."
                  className="w-full px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={isSaving}
              className="py-2.5 px-5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors border border-slate-700"
            >
              Update Profile
            </button>
          </form>

          {/* Account Actions: Logout & Delete Account */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setIsLogoutOpen(true)}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white px-3 py-2 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Log out</span>
            </button>

            <button
              type="button"
              onClick={() => setIsDeleteAccountOpen(true)}
              className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 px-3 py-2 rounded-xl hover:bg-rose-950/30 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete account</span>
            </button>
          </div>
        </section>
      </div>

      {/* Logout Confirmation Modal */}
      <ConfirmDialog
        isOpen={isLogoutOpen}
        onClose={() => setIsLogoutOpen(false)}
        onConfirm={handleLogout}
        title="Leaving already? 😄"
        message="Sakhi will be right here whenever you want to talk or learn again."
        confirmText="Logout"
        cancelText="Stay"
        icon="👋"
      />

      {/* Delete Account Confirmation Modal */}
      <ConfirmDialog
        isOpen={isDeleteAccountOpen}
        onClose={() => setIsDeleteAccountOpen(false)}
        onConfirm={handleDeleteAccount}
        title="Delete your account?"
        message="This action is permanent and irreversible. Your conversations, memories, and personal settings will be permanently erased from MySQL."
        confirmText="Delete Account"
        isDestructive={true}
        icon="⚠️"
      />
    </div>
  );
};
