import React, { useEffect, useRef } from 'react';

interface VoiceWaveformProps {
  active: boolean;
  frequency?: number; // 0 to 1
  barsCount?: number;
  className?: string;
}

export const VoiceWaveform: React.FC<VoiceWaveformProps> = ({
  active,
  frequency = 0,
  barsCount = 18,
  className = '',
}) => {
  const bars = Array.from({ length: barsCount });

  return (
    <div className={`flex items-center justify-center gap-1.5 h-12 py-2 px-4 ${className}`}>
      {bars.map((_, i) => {
        // Compute wave height variation
        const distanceToCenter = Math.abs(i - barsCount / 2) / (barsCount / 2);
        const centerFactor = 1 - distanceToCenter * 0.65;
        
        let heightPercent = 15;
        if (active) {
          const jitter = Math.sin((i * 0.8) + (Date.now() / 120)) * 0.35 + 0.65;
          const dynamicFactor = Math.max(0.15, frequency * jitter * centerFactor);
          heightPercent = Math.min(100, Math.max(15, dynamicFactor * 100));
        }

        return (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-100 ${
              active
                ? 'bg-gradient-to-t from-rose-500 via-pink-400 to-purple-400 shadow-[0_0_8px_rgba(244,63,94,0.6)]'
                : 'bg-slate-700/60'
            }`}
            style={{
              height: `${heightPercent}%`,
              transition: 'height 0.08s ease-out',
            }}
          />
        );
      })}
    </div>
  );
};
