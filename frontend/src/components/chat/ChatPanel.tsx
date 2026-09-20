import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Mic, Sparkles, ArrowLeft } from 'lucide-react';
import { Message } from '../../types';
import { MessageBubble } from './MessageBubble';
import { useVoice } from '../../context/VoiceContext';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  messages: Message[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  friendName?: string;
  voiceId?: string;
  gender?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  isOpen,
  onClose,
  messages,
  onSendMessage,
  isLoading,
  friendName = 'Sakhi',
  voiceId = 'female_voice',
  gender = 'female'
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const { isRecording, startListening, stopListening } = useVoice();

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleMicVoiceInput = (text: string) => {
    if (text.trim()) {
      onSendMessage(text.trim());
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopListening();
    } else {
      startListening(handleMicVoiceInput);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-out Natural Conversations Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-[#0B0F19]/95 border-l border-slate-800 shadow-2xl backdrop-blur-2xl flex flex-col transition-all duration-300 animate-slideInRight">
        {/* Header (Matching Reference Screenshot Panel 6) */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/80 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h3 className="font-bold text-white text-base leading-snug">
                Natural Conversations
              </h3>
              <p className="text-[11px] text-slate-400">
                Only your language, no symbol descriptions
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close chat"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 text-slate-400">
              <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-pink-500/40 mb-3 shadow-lg">
                <img
                  src={gender === 'male' ? '/characters/male_idle.jpg' : '/characters/female_idle.jpg'}
                  alt={friendName}
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-sm font-semibold text-slate-200">
                Start talking or typing with {friendName}!
              </p>
              <p className="text-xs text-slate-400 mt-1 max-w-xs">
                Telugu, English, or Tanglish — {friendName} replies naturally in the same language without duplicate translations 💜
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                friendName={friendName}
                voiceId={voiceId}
                gender={gender}
              />
            ))
          )}

          {/* Thinking / Loading State */}
          {isLoading && (
            <div className="flex items-center gap-2 text-slate-400 text-xs italic py-2 ml-10 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-bounce" />
              <span>{friendName} is thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Message Input Bar (Matching Reference Screenshot Panel 6) */}
        <form
          onSubmit={handleSubmit}
          className="p-3.5 sm:p-4 border-t border-slate-800/80 bg-slate-900/70 flex items-center gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 rounded-full bg-slate-950/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder:text-slate-500"
          />

          {/* Voice Mic Button */}
          <button
            type="button"
            onClick={toggleMic}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
              isRecording
                ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/50 animate-pulse'
                : 'bg-purple-900/60 hover:bg-purple-800 border border-purple-500/30 text-purple-200'
            }`}
          >
            <Mic className="w-4.5 h-4.5" />
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-500 hover:opacity-95 text-white flex items-center justify-center shadow-md disabled:opacity-30 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </>
  );
};
