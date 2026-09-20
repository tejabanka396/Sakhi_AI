import React from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { FriendState } from '../../types';

interface MicrophoneButtonProps {
  isRecording: boolean;
  isSpeaking: boolean;
  friendState: FriendState;
  audioFrequency?: number;
  onPress: () => void;
  onStopSpeaking?: () => void;
  disabled?: boolean;
}

export const MicrophoneButton: React.FC<MicrophoneButtonProps> = ({
  isRecording,
  isSpeaking,
  friendState,
  audioFrequency = 0,
  onPress,
  onStopSpeaking,
  disabled = false,
}) => {
  const active = isRecording || isSpeaking;
  const leftBars = [0.25, 0.45, 0.8, 0.55, 0.35, 0.2];
  const rightBars = [0.2, 0.35, 0.55, 0.8, 0.45, 0.25];

  return (
    <div className="flex items-center justify-center gap-3 sm:gap-5 select-none">
      {/* Left Sound Waveform Bars */}
      <div className="flex items-center gap-1 sm:gap-1.5 h-12">
        {leftBars.map((heightRatio, idx) => {
          const height = active
            ? Math.max(12, Math.min(46, (audioFrequency * 1.4 + heightRatio) * 32))
            : heightRatio * 20;
          return (
            <div
              key={`left-${idx}`}
              className={`w-1 rounded-full transition-all duration-100 ${
                active
                  ? 'bg-gradient-to-t from-cyan-400 via-purple-400 to-white shadow-[0_0_8px_rgba(34,211,238,0.7)]'
                  : 'bg-white/40'
              }`}
              style={{ height: `${height}px` }}
            />
          );
        })}
      </div>

      {/* Center Glowing Microphone Button (Reference Screenshot Style) */}
      <div className="relative flex items-center justify-center">
        {/* Outer Atmospheric Glow */}
        <div
          className={`absolute -inset-3 rounded-full blur-xl transition-all duration-500 pointer-events-none ${
            isSpeaking
              ? 'bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-500 opacity-80 scale-125 animate-pulse'
              : isRecording
              ? 'bg-gradient-to-r from-rose-500 via-pink-500 to-cyan-400 opacity-90 scale-130 animate-pulse'
              : friendState === 'thinking'
              ? 'bg-purple-600/60 opacity-75 animate-pulse'
              : 'bg-gradient-to-r from-pink-500/50 via-purple-600/50 to-cyan-500/40 opacity-60 scale-110'
          }`}
        />

        {/* Concentric Neon Ring */}
        <div className="absolute inset-0 rounded-full border-2 border-white/30 shadow-[0_0_20px_rgba(236,72,153,0.5)] pointer-events-none" />

        {/* Ripple Effect for active listening */}
        {isRecording && (
          <span className="absolute -inset-2 rounded-full border border-pink-400/60 animate-ping pointer-events-none" />
        )}

        {/* Action Button */}
        <button
          onClick={isSpeaking && onStopSpeaking ? onStopSpeaking : onPress}
          disabled={disabled || friendState === 'thinking'}
          aria-label={
            isSpeaking
              ? 'Stop speaking'
              : isRecording
              ? 'Stop listening'
              : 'Tap to talk'
          }
          className={`relative z-10 w-18 h-18 sm:w-20 sm:h-20 rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none shadow-2xl ${
            isSpeaking
              ? 'bg-gradient-to-tr from-purple-700 via-indigo-600 to-pink-600 text-white scale-105 shadow-[0_0_35px_rgba(168,85,247,0.6)]'
              : isRecording
              ? 'bg-gradient-to-tr from-rose-600 via-pink-500 to-purple-600 text-white scale-110 shadow-[0_0_40px_rgba(244,63,94,0.7)]'
              : friendState === 'thinking'
              ? 'bg-slate-800 text-purple-300 cursor-wait'
              : 'bg-gradient-to-tr from-purple-600 via-pink-500 to-rose-500 hover:scale-105 text-white shadow-[0_0_30px_rgba(236,72,153,0.5)]'
          }`}
        >
          {friendState === 'thinking' ? (
            <Loader2 className="w-8 h-8 animate-spin text-purple-300" />
          ) : isSpeaking ? (
            <Square className="w-7 h-7 sm:w-8 sm:h-8 fill-current" />
          ) : (
            <Mic className="w-8 h-8 sm:w-9 sm:h-9" />
          )}
        </button>
      </div>

      {/* Right Sound Waveform Bars */}
      <div className="flex items-center gap-1 sm:gap-1.5 h-12">
        {rightBars.map((heightRatio, idx) => {
          const height = active
            ? Math.max(12, Math.min(46, (audioFrequency * 1.4 + heightRatio) * 32))
            : heightRatio * 20;
          return (
            <div
              key={`right-${idx}`}
              className={`w-1 rounded-full transition-all duration-100 ${
                active
                  ? 'bg-gradient-to-t from-purple-400 via-pink-400 to-white shadow-[0_0_8px_rgba(236,72,153,0.7)]'
                  : 'bg-white/40'
              }`}
              style={{ height: `${height}px` }}
            />
          );
        })}
      </div>
    </div>
  );
};
