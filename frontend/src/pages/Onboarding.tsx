import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ArrowLeft, ArrowRight, Volume2, Square, Loader2, Sparkles, Mic } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useVoice } from '../context/VoiceContext';
import { getVoiceForGender, getVoiceLabel, getVoiceDescription } from '../services/voice';
import { Gender } from '../types';

export const Onboarding: React.FC = () => {
  const navigate = useNavigate();
  const { user, friendProfile, updateFriendProfile, updateSettings, updateUser, setOnboardingCompleted } = useAuth();
  const { success, error: toastError } = useToast();
  const { previewVoice, stopSpeaking, isSpeaking } = useVoice();

  const [step, setStep] = useState<number>(1);
  const [userName, setUserName] = useState<string>(user?.name || '');
  const [friendNameChoice, setFriendNameChoice] = useState<'default' | 'custom'>('default');
  const [customFriendName, setCustomFriendName] = useState<string>('');
  const [gender, setGender] = useState<Gender>(friendProfile?.gender || 'female');

  // Audio preview state
  const [previewingVoice, setPreviewingVoice] = useState<string | null>(null);
  const [loadingVoice, setLoadingVoice] = useState<string | null>(null);

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

  const handlePlayPreview = async (voiceId: string) => {
    if (previewingVoice === voiceId) {
      stopSpeaking();
      setPreviewingVoice(null);
      return;
    }

    try {
      setLoadingVoice(voiceId);
      setPreviewingVoice(voiceId);
      await previewVoice(voiceId);
    } catch {
      toastError('Voice preview unavailable.');
      setPreviewingVoice(null);
    } finally {
      setLoadingVoice(null);
    }
  };

  const activeFriendName =
    friendNameChoice === 'default'
      ? gender === 'female'
        ? 'Sakhi'
        : 'Sakha'
      : customFriendName.trim() || (gender === 'female' ? 'Sakhi' : 'Sakha');

  const handleComplete = async () => {
    try {
      const activeVoiceId = getVoiceForGender(gender);
      await Promise.all([
        updateUser({ name: userName.trim() || 'Friend' }),
        updateFriendProfile({
          friend_name: activeFriendName,
          gender,
          voice_id: activeVoiceId,
        }),
        updateSettings({
          default_mode: 'talk',
          voice_enabled: true,
          language_preference: 'auto'
        }),
      ]);
      setOnboardingCompleted(true);
      success(`Welcome ${userName || 'Friend'}! ${activeFriendName} is ready 💜`);
      navigate('/home');
    } catch {
      setOnboardingCompleted(true);
      navigate('/home');
    }
  };

  const currentVoiceId = getVoiceForGender(gender);
  const isCurrentPreviewPlaying = previewingVoice === currentVoiceId;
  const isCurrentPreviewLoading = loadingVoice === currentVoiceId;

  return (
    <div className="min-h-screen bg-[#070B14] text-white flex flex-col items-center justify-center p-4 sm:p-6 select-none relative overflow-hidden">
      {/* 1. Deep Atmospheric Gradient & Particle Glows */}
      <div className="absolute -top-32 left-1/4 w-[600px] h-[600px] bg-purple-900/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[500px] h-[500px] bg-pink-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute -bottom-32 left-1/3 w-[550px] h-[550px] bg-cyan-600/15 rounded-full blur-[130px] pointer-events-none" />

      {/* Step Indicator Dots (3 Steps) */}
      <div className="absolute top-6 flex items-center gap-2 z-20">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`h-2 rounded-full transition-all duration-300 ${
              s === step
                ? 'w-8 bg-gradient-to-r from-pink-500 to-purple-500'
                : s < step
                ? 'w-2.5 bg-pink-500/60'
                : 'w-2 bg-slate-800'
            }`}
          />
        ))}
      </div>

      {/* Main Interactive Card Frame */}
      <div className="w-full max-w-2xl flex flex-col items-center text-center z-10 animate-fadeIn my-auto">
        {/* ========================================================= */}
        {/* STEP 1: Personal Dynamic Names */}
        {/* ========================================================= */}
        {step === 1 && (
          <div className="flex flex-col items-center space-y-6 w-full max-w-lg">
            <div className="relative w-28 h-28 rounded-3xl overflow-hidden border-2 border-purple-500/40 shadow-[0_0_25px_rgba(168,85,247,0.3)]">
              <img
                src="/characters/female_idle.jpg"
                alt="Sakhi"
                className="w-full h-full object-cover"
              />
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-purple-100 to-pink-200 bg-clip-text text-transparent">
                Welcome to Sakhi AI
              </h1>
              <p className="text-slate-300 text-sm sm:text-base">
                Your personal AI companion. First, what should I call you?
              </p>
            </div>

            <div className="w-full max-w-md space-y-4">
              <div className="text-left">
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 ml-1">
                  Your Name
                </label>
                <input
                  type="text"
                  autoFocus
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="e.g. Teja, Rahul, Priya..."
                  className="w-full px-5 py-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/80 text-white text-base font-medium focus:outline-none focus:border-pink-500 focus:ring-2 focus:ring-pink-500/30 transition-all shadow-inner"
                />
              </div>

              <div className="text-left">
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 ml-1">
                  Companion Name
                </label>
                <div className="grid grid-cols-2 gap-3 mb-2">
                  <button
                    type="button"
                    onClick={() => setFriendNameChoice('default')}
                    className={`py-3 px-4 rounded-xl border text-sm font-semibold transition-all ${
                      friendNameChoice === 'default'
                        ? 'bg-gradient-to-r from-pink-500/20 to-purple-600/20 border-pink-500 text-white ring-1 ring-pink-500/50 shadow-md'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Default ({gender === 'female' ? 'Sakhi' : 'Sakha'})
                  </button>
                  <button
                    type="button"
                    onClick={() => setFriendNameChoice('custom')}
                    className={`py-3 px-4 rounded-xl border text-sm font-semibold transition-all ${
                      friendNameChoice === 'custom'
                        ? 'bg-gradient-to-r from-pink-500/20 to-purple-600/20 border-pink-500 text-white ring-1 ring-pink-500/50 shadow-md'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Custom Name
                  </button>
                </div>

                {friendNameChoice === 'custom' && (
                  <input
                    type="text"
                    value={customFriendName}
                    onChange={(e) => setCustomFriendName(e.target.value)}
                    placeholder="e.g. Anu, Lucky, Buddy..."
                    className="w-full px-5 py-3 rounded-xl bg-slate-900/90 border border-pink-500/60 text-white text-sm focus:outline-none focus:ring-2 focus:ring-pink-500/40"
                  />
                )}
              </div>
            </div>

            <button
              onClick={() => {
                if (!userName.trim()) return;
                setStep(2);
              }}
              disabled={!userName.trim()}
              className="mt-4 w-full max-w-md py-4 px-8 rounded-full bg-gradient-to-r from-pink-500 via-rose-500 to-purple-600 hover:opacity-95 text-white font-bold text-base shadow-[0_0_30px_rgba(244,63,94,0.4)] disabled:opacity-40 transition-all flex items-center justify-center gap-2"
            >
              <span>Continue</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* ========================================================= */}
        {/* STEP 2: Choose Your Character (With Automatic Voice Binding) */}
        {/* ========================================================= */}
        {step === 2 && (
          <div className="flex flex-col items-center w-full max-w-xl">
            {/* Header with back button */}
            <div className="relative w-full flex items-center justify-center mb-6">
              <button
                onClick={() => {
                  stopSpeaking();
                  setStep(1);
                }}
                className="absolute left-0 p-2 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <div>
                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Choose Your Character
                </h2>
                <p className="text-slate-400 text-xs sm:text-sm mt-1">
                  Select your companion's appearance & personality
                </p>
              </div>
            </div>

            {/* Two Large Cards Side-by-Side (Female vs Male) */}
            <div className="grid grid-cols-2 gap-4 sm:gap-6 w-full mb-6">
              {/* Female Card */}
              <div
                onClick={() => {
                  stopSpeaking();
                  setGender('female');
                }}
                className={`relative cursor-pointer rounded-3xl p-4 sm:p-5 flex flex-col items-center text-center transition-all duration-300 border-2 overflow-hidden ${
                  gender === 'female'
                    ? 'bg-gradient-to-b from-purple-950/60 to-slate-900/90 border-purple-500/90 shadow-[0_0_35px_rgba(168,85,247,0.35)] scale-[1.02]'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 opacity-80 hover:opacity-100'
                }`}
              >
                {/* Active Check Indicator */}
                {gender === 'female' && (
                  <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-white shadow-lg ring-2 ring-purple-400/50">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}

                {/* Character Image */}
                <div className="w-full aspect-square rounded-2xl overflow-hidden mb-3 border border-white/10 shadow-lg">
                  <img
                    src="/characters/female_idle.jpg"
                    alt="Female Sakhi"
                    className="w-full h-full object-cover"
                  />
                </div>

                <h3 className="text-lg sm:text-xl font-bold text-white mb-0.5">Female</h3>
                <p className="text-xs text-slate-300 font-medium line-clamp-1">
                  Kind, friendly and supportive
                </p>
              </div>

              {/* Male Card */}
              <div
                onClick={() => {
                  stopSpeaking();
                  setGender('male');
                }}
                className={`relative cursor-pointer rounded-3xl p-4 sm:p-5 flex flex-col items-center text-center transition-all duration-300 border-2 overflow-hidden ${
                  gender === 'male'
                    ? 'bg-gradient-to-b from-blue-950/60 to-slate-900/90 border-cyan-400/90 shadow-[0_0_35px_rgba(34,211,238,0.35)] scale-[1.02]'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 opacity-80 hover:opacity-100'
                }`}
              >
                {/* Active Check Indicator */}
                {gender === 'male' && (
                  <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center text-white shadow-lg ring-2 ring-cyan-300/50">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}

                {/* Character Image */}
                <div className="w-full aspect-square rounded-2xl overflow-hidden mb-3 border border-white/10 shadow-lg">
                  <img
                    src="/characters/male_idle.jpg"
                    alt="Male Sakha"
                    className="w-full h-full object-cover"
                  />
                </div>

                <h3 className="text-lg sm:text-xl font-bold text-white mb-0.5">Male</h3>
                <p className="text-xs text-slate-300 font-medium line-clamp-1">
                  Calm, smart and motivating
                </p>
              </div>
            </div>

            {/* Voice Confirmation Callout with Direct Preview Button */}
            <div className="w-full bg-slate-900/90 border border-purple-500/30 rounded-2xl p-4 mb-8 flex flex-col sm:flex-row items-center justify-between gap-3 backdrop-blur-md shadow-lg">
              <div className="flex items-center gap-3 text-left">
                <div className="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center shrink-0">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-semibold text-white">
                    {gender === 'female'
                      ? 'Female selected — Female Voice will be used automatically'
                      : 'Male selected — Male Voice will be used automatically'}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {getVoiceDescription(gender)}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handlePlayPreview(currentVoiceId)}
                className={`py-2 px-4 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shrink-0 ${
                  isCurrentPreviewPlaying
                    ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg animate-pulse'
                    : isCurrentPreviewLoading
                    ? 'bg-slate-800 text-pink-300'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                }`}
              >
                {isCurrentPreviewLoading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : isCurrentPreviewPlaying ? (
                  <Square className="w-3.5 h-3.5 fill-current" />
                ) : (
                  <Volume2 className="w-3.5 h-3.5 text-pink-400" />
                )}
                <span>{isCurrentPreviewLoading ? 'Loading...' : isCurrentPreviewPlaying ? 'Stop Voice' : `Preview ${getVoiceLabel(gender)}`}</span>
              </button>
            </div>

            {/* Glowing Pill Continue Button */}
            <button
              onClick={() => {
                stopSpeaking();
                setStep(3);
              }}
              className="w-full max-w-sm py-4 px-8 rounded-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 hover:opacity-95 text-white font-bold text-base shadow-[0_0_30px_rgba(236,72,153,0.4)] transition-all flex items-center justify-center gap-2"
            >
              <span>Continue</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* ========================================================= */}
        {/* STEP 3: Ready to Talk / All Set */}
        {/* ========================================================= */}
        {step === 3 && (
          <div className="flex flex-col items-center space-y-6 w-full max-w-md">
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(244,63,94,0.4)] ring-4 ring-pink-500/20 animate-pulse">
              <Mic className="w-10 h-10 text-white" />
            </div>

            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tight text-white">
                All Set, {userName}!
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                {activeFriendName} is ready with {getVoiceLabel(gender).toLowerCase()} to be your real friend, study buddy, and companion.
                Tap below to start talking!
              </p>
            </div>

            <button
              onClick={handleComplete}
              className="w-full py-4 px-8 rounded-full bg-gradient-to-r from-pink-500 via-rose-500 to-purple-600 hover:opacity-95 text-white font-bold text-lg shadow-[0_0_35px_rgba(244,63,94,0.5)] transition-all flex items-center justify-center gap-2"
            >
              <span>Start Talking to {activeFriendName} 💜</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
