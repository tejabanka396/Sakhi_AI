import React, { useState } from 'react';
import { Volume2, VolumeX, Copy, Bookmark, Check, CheckCheck } from 'lucide-react';
import { Message } from '../../types';
import { useToast } from '../../context/ToastContext';
import { useVoice } from '../../context/VoiceContext';
import { memoryService } from '../../services/memory';

interface MessageBubbleProps {
  message: Message;
  friendName?: string;
  voiceId?: string;
  gender?: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  friendName = 'Sakhi',
  voiceId = 'female_voice',
  gender = 'female'
}) => {
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const { success, error } = useToast();
  const { speakResponse, isSpeaking, stopSpeaking } = useVoice();

  const isUser = message.sender === 'user';

  // Format time (e.g. 10:25 PM)
  const formatTime = (isoString?: string) => {
    try {
      const date = isoString ? new Date(isoString) : new Date();
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '10:25 PM';
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    success('Copied to clipboard ✓');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReplay = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else {
      speakResponse({
        response_id: `replay_${message.id}_${Date.now()}`,
        speech_text: message.content,
        voiceId
      });
    }
  };

  const handleSaveToMemory = async () => {
    try {
      await memoryService.add(message.content, 'personal');
      setSaved(true);
      success('Saved to Sakhi memory 💜');
    } catch {
      error('Failed to save memory.');
    }
  };

  return (
    <div className={`group flex flex-col ${isUser ? 'items-end' : 'items-start'} mb-3.5 w-full`}>
      <div className={`flex items-end gap-2 max-w-[88%] sm:max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full overflow-hidden border border-white/15 shrink-0 mb-1 shadow-md">
          {isUser ? (
            <div className="w-full h-full bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-xs font-bold text-white">
              U
            </div>
          ) : (
            <img
              src={gender === 'male' ? '/characters/male_idle.jpg' : '/characters/female_idle.jpg'}
              alt={friendName}
              className="w-full h-full object-cover"
            />
          )}
        </div>

        {/* Message Bubble Card */}
        <div
          className={`relative px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-lg transition-all ${
            isUser
              ? 'bg-[#1E293B]/90 border border-blue-500/30 text-slate-100 rounded-br-none'
              : 'bg-[#0F172A]/90 border border-slate-800 text-slate-100 rounded-bl-none shadow-[0_4px_20px_rgba(0,0,0,0.3)]'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>

          {/* Timestamp & Icons Footer */}
          <div className={`flex items-center gap-1.5 mt-1 text-[11px] ${isUser ? 'justify-end text-cyan-300/80' : 'justify-end text-slate-400'}`}>
            <span>{formatTime(message.created_at)}</span>

            {isUser ? (
              <CheckCheck className="w-3.5 h-3.5 text-cyan-400 inline" />
            ) : (
              <button
                onClick={handleReplay}
                title="Hear audio"
                className="hover:text-pink-400 transition-colors p-0.5"
              >
                <Volume2 className="w-3.5 h-3.5 inline" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons for Assistant Message */}
      {!isUser && (
        <div className="flex items-center gap-2 mt-1 ml-10 opacity-60 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleReplay}
            className="p-1 hover:bg-slate-800/60 rounded-lg text-slate-400 hover:text-white transition-colors text-[11px] flex items-center gap-1"
          >
            <Volume2 className="w-3 h-3" />
            <span>Speak</span>
          </button>
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-slate-800/60 rounded-lg text-slate-400 hover:text-white transition-colors text-[11px] flex items-center gap-1"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={handleSaveToMemory}
            className="p-1 hover:bg-slate-800/60 rounded-lg text-slate-400 hover:text-pink-400 transition-colors text-[11px] flex items-center gap-1"
          >
            <Bookmark className={`w-3 h-3 ${saved ? 'text-pink-400 fill-current' : ''}`} />
            <span>{saved ? 'Saved' : 'Save'}</span>
          </button>
        </div>
      )}
    </div>
  );
};
