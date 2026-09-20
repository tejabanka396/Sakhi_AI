import React, { useState, useEffect, useMemo } from 'react';
import { FriendState, Gender } from '../../types';

interface AnimatedCharacterProps {
  gender?: Gender;
  friendName?: string;
  state?: FriendState;
  audioFrequency?: number; // 0.0 to 1.0 for audio lip-sync
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
  onRetry?: () => void;
  showBadges?: boolean;
}

export const AnimatedCharacter: React.FC<AnimatedCharacterProps> = ({
  gender = 'female',
  friendName = 'Sakhi',
  state = 'idle',
  audioFrequency = 0,
  size = 'lg',
  className = '',
  onRetry,
  showBadges = false
}) => {
  const [isBlinking, setIsBlinking] = useState(false);
  const [imgError, setImgError] = useState(false);

  // 1. Natural realistic blinking timer with randomized intervals (every 2.8s to 4.8s)
  useEffect(() => {
    let timeoutId: any;
    const scheduleNextBlink = () => {
      const delay = 2800 + Math.random() * 2200;
      timeoutId = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          scheduleNextBlink();
        }, 150);
      }, delay);
    };

    scheduleNextBlink();
    return () => clearTimeout(timeoutId);
  }, []);

  const isFemale = gender === 'female';

  // Sizing definitions
  const sizeClasses = {
    xs: 'w-16 h-16',
    sm: 'w-24 h-24 sm:w-28 sm:h-28',
    md: 'w-40 h-40 sm:w-48 sm:h-48',
    lg: 'w-64 h-64 sm:w-72 sm:h-72',
    xl: 'w-72 h-72 sm:w-84 sm:h-84 md:w-96 md:h-96',
    full: 'w-full h-full'
  }[size];

  // Image source based on gender and state
  const imageSrc = useMemo(() => {
    const prefix = isFemale ? '/characters/female_' : '/characters/male_';
    switch (state) {
      case 'listening':
        return `${prefix}listening.jpg`;
      case 'thinking':
        return `${prefix}thinking.jpg`;
      case 'speaking':
        return `${prefix}speaking.jpg`;
      case 'happy':
        return `${prefix}happy.jpg`;
      case 'idle':
      default:
        return `${prefix}idle.jpg`;
    }
  }, [isFemale, state]);

  // Dynamic speaking mouth scale from audio amplitude
  const speechScale = useMemo(() => {
    if (state === 'speaking') {
      return 1 + Math.min(0.04, audioFrequency * 0.08);
    }
    return 1;
  }, [state, audioFrequency]);

  return (
    <div className={`relative flex flex-col items-center justify-center select-none ${className}`}>
      {/* 1. Atmospheric Ambient Glow & State Ring */}
      <div
        className={`absolute -inset-4 rounded-full transition-all duration-700 blur-2xl pointer-events-none ${
          state === 'speaking'
            ? 'bg-gradient-to-tr from-pink-500/30 via-purple-600/35 to-cyan-400/30 scale-110 animate-pulse'
            : state === 'listening'
            ? 'bg-gradient-to-tr from-cyan-400/35 via-blue-500/30 to-purple-500/25 scale-105'
            : state === 'thinking'
            ? 'bg-gradient-to-tr from-purple-500/25 via-indigo-500/20 to-pink-500/20 animate-pulse'
            : state === 'happy'
            ? 'bg-gradient-to-tr from-pink-400/35 via-rose-500/30 to-amber-400/25 scale-105'
            : 'bg-purple-600/15'
        }`}
      />

      {/* 2. Listening Halo Ring (matching Reference Screenshot Listening state) */}
      {state === 'listening' && (
        <div className="absolute -top-3 w-3/4 h-3/4 rounded-full border-2 border-cyan-400/60 shadow-[0_0_20px_rgba(34,211,238,0.5)] animate-spin [animation-duration:8s] pointer-events-none z-10" />
      )}

      {/* 3. Speaking Dynamic Side Waveforms (matching Reference Screenshot Speaking state) */}
      {state === 'speaking' && (
        <>
          {/* Left Audio Waveform Bars */}
          <div className="absolute -left-7 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-1 z-20 pointer-events-none">
            <span className="w-1 h-3 bg-cyan-400 rounded-full animate-bounce [animation-delay:0.1s]" />
            <span className="w-1 h-7 bg-purple-400 rounded-full animate-bounce [animation-delay:0.3s]" />
            <span className="w-1 h-10 bg-pink-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            <span className="w-1 h-5 bg-cyan-300 rounded-full animate-bounce [animation-delay:0.4s]" />
          </div>
          {/* Right Audio Waveform Bars */}
          <div className="absolute -right-7 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-1 z-20 pointer-events-none">
            <span className="w-1 h-5 bg-cyan-300 rounded-full animate-bounce [animation-delay:0.4s]" />
            <span className="w-1 h-10 bg-pink-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            <span className="w-1 h-7 bg-purple-400 rounded-full animate-bounce [animation-delay:0.3s]" />
            <span className="w-1 h-3 bg-cyan-400 rounded-full animate-bounce [animation-delay:0.1s]" />
          </div>
        </>
      )}

      {/* 4. Happy / Laughing Floating Hearts (matching Reference Screenshot) */}
      {state === 'happy' && (
        <div className="absolute inset-0 pointer-events-none z-20 overflow-visible">
          <span className="absolute -top-2 left-6 text-pink-400 text-lg animate-bounce [animation-duration:2s]">💜</span>
          <span className="absolute -top-4 right-8 text-pink-300 text-sm animate-pulse [animation-duration:1.5s]">✨</span>
          <span className="absolute top-8 -right-3 text-rose-400 text-base animate-bounce [animation-duration:2.3s]">💖</span>
        </div>
      )}

      {/* 5. Main Character Portrait Card with Smooth Motion */}
      <div
        className={`relative ${sizeClasses} rounded-3xl overflow-hidden border-2 transition-all duration-500 shadow-2xl flex items-center justify-center ${
          state === 'speaking'
            ? 'border-pink-500/70 shadow-[0_0_35px_rgba(244,63,94,0.4)]'
            : state === 'listening'
            ? 'border-cyan-400/80 shadow-[0_0_30px_rgba(34,211,238,0.45)]'
            : state === 'thinking'
            ? 'border-purple-400/60 shadow-[0_0_25px_rgba(168,85,247,0.35)]'
            : 'border-purple-500/30 shadow-[0_0_20px_rgba(147,51,234,0.2)]'
        }`}
        style={{
          transform: `scale(${speechScale}) ${
            state === 'thinking' ? 'rotate(1.5deg)' : state === 'listening' ? 'translateY(-2px)' : 'translateY(0)'
          }`
        }}
      >
        {!imgError ? (
          <div className="relative w-full h-full overflow-hidden">
            {/* Base Character Image with Hair & Breathing Motion */}
            <img
              src={imageSrc}
              alt={`${friendName} (${gender})`}
              className={`w-full h-full object-cover object-center transition-all duration-500 ${
                state === 'idle' ? 'animate-breathing' : ''
              }`}
              style={{
                filter:
                  state === 'speaking'
                    ? 'brightness(1.05) contrast(1.02)'
                    : state === 'listening'
                    ? 'brightness(1.03)'
                    : 'brightness(1.0)'
              }}
              onError={() => setImgError(true)}
            />

            {/* Subtle Eyelid Blinking Overlay */}
            <div
              className={`absolute inset-0 bg-slate-900/40 pointer-events-none transition-opacity duration-150 ${
                isBlinking && state !== 'happy' ? 'opacity-85' : 'opacity-0'
              }`}
              style={{
                clipPath: 'ellipse(42% 16% at 50% 38%)'
              }}
            />

            {/* Soft Ambient Inner Vignette */}
            <div className="absolute inset-0 rounded-3xl pointer-events-none ring-1 ring-inset ring-white/15 bg-gradient-to-t from-slate-950/60 via-transparent to-white/5" />
          </div>
        ) : (
          /* Fallback Elegant Avatar if assets are loading */
          <div className="w-full h-full bg-gradient-to-tr from-slate-900 via-purple-950 to-slate-900 flex flex-col items-center justify-center text-center p-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mb-2 shadow-lg">
              {friendName.charAt(0)}
            </div>
            <p className="text-xs text-purple-200 font-medium">{friendName}</p>
          </div>
        )}
      </div>

      {/* 6. State Indicator Pill (optional for panels) */}
      {showBadges && (
        <div className="mt-3 px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-md border border-white/10 flex items-center gap-1.5 shadow-lg bg-slate-900/80 text-slate-200">
          <span
            className={`w-2 h-2 rounded-full ${
              state === 'speaking'
                ? 'bg-pink-400 animate-ping'
                : state === 'listening'
                ? 'bg-cyan-400 animate-pulse'
                : state === 'thinking'
                ? 'bg-purple-400 animate-pulse'
                : 'bg-emerald-400'
            }`}
          />
          <span className="capitalize">{state}</span>
        </div>
      )}
    </div>
  );
};
