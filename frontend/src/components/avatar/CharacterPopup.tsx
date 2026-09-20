import React from 'react';
import { Volume2, VolumeX, X, Sparkles } from 'lucide-react';
import { AnimatedCharacter } from './AnimatedCharacter';
import { Gender, FriendState } from '../../types';

interface CharacterPopupProps {
  isOpen: boolean;
  onClose: () => void;
  friendName: string;
  gender: Gender;
  state: FriendState;
  audioFrequency?: number;
  currentSpeechText?: string;
  onStopSpeaking?: () => void;
}

export const CharacterPopup: React.FC<CharacterPopupProps> = ({
  isOpen,
  onClose,
  friendName,
  gender,
  state,
  audioFrequency = 0,
  currentSpeechText,
  onStopSpeaking
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed bottom-24 right-4 sm:right-8 z-50 animate-scaleUp pointer-events-auto">
      {/* Floating Glassmorphism Character Card */}
      <div className="relative p-3.5 sm:p-4 rounded-3xl bg-slate-900/90 border border-pink-500/30 backdrop-blur-2xl shadow-[0_15px_40px_rgba(0,0,0,0.6)] flex flex-col items-center max-w-[280px] sm:max-w-xs ring-1 ring-white/10">
        {/* Atmospheric Glow behind popup */}
        <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-pink-500/20 via-purple-600/20 to-cyan-500/20 blur-lg pointer-events-none -z-10" />

        {/* Header Bar */}
        <div className="flex items-center justify-between w-full mb-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-pink-400 animate-ping" />
            <span className="text-xs font-semibold text-pink-300 tracking-wide">{friendName} is speaking</span>
          </div>

          <div className="flex items-center gap-1">
            {onStopSpeaking && (
              <button
                onClick={onStopSpeaking}
                title="Stop voice"
                className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 transition-colors"
              >
                <VolumeX className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={onClose}
              title="Minimize popup"
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Character Avatar in Speaking/Active state */}
        <div className="relative my-1">
          <AnimatedCharacter
            gender={gender}
            friendName={friendName}
            state={state}
            audioFrequency={audioFrequency}
            size="md"
          />
        </div>

        {/* Spoken subtitle / caption if present */}
        {currentSpeechText && (
          <div className="mt-2.5 px-3 py-1.5 rounded-2xl bg-slate-950/70 border border-white/5 text-center text-xs text-slate-200 line-clamp-3 leading-relaxed">
            "{currentSpeechText}"
          </div>
        )}

        {/* Mini waveform footer */}
        <div className="flex items-center gap-1 mt-2.5">
          <span className="w-1 h-2 bg-pink-400 rounded-full animate-bounce [animation-delay:0.1s]" />
          <span className="w-1 h-3.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0.3s]" />
          <span className="w-1 h-5 bg-cyan-400 rounded-full animate-bounce [animation-delay:0.2s]" />
          <span className="w-1 h-3.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]" />
          <span className="w-1 h-2 bg-purple-400 rounded-full animate-bounce [animation-delay:0.15s]" />
        </div>
      </div>
    </div>
  );
};
