import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Brain, Settings as SettingsIcon, User as UserIcon, History, Sparkles, Volume2, VolumeX } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useVoice } from '../context/VoiceContext';
import { useToast } from '../context/ToastContext';
import { AnimatedCharacter } from '../components/avatar/AnimatedCharacter';
import { CharacterPopup } from '../components/avatar/CharacterPopup';
import { MicrophoneButton } from '../components/voice/MicrophoneButton';
import { ChatPanel } from '../components/chat/ChatPanel';
import { chatService } from '../services/chat';
import { getVoiceForGender } from '../services/voice';
import { Message } from '../types';

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { user, friendProfile, settings } = useAuth();
  const {
    friendState,
    setFriendState,
    isRecording,
    isSpeaking,
    audioFrequency,
    transcript,
    startListening,
    stopListening,
    speakResponse,
    stopSpeaking,
    interrupt
  } = useVoice();
  const { error: toastError } = useToast();

  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [currentAiReply, setCurrentAiReply] = useState<string>('');
  const [isPopupVisible, setIsPopupVisible] = useState(false);

  // Dynamic user and friend names (Requirement 13)
  const userName = user?.name || 'Friend';
  const friendName = friendProfile?.friend_name || (friendProfile?.gender === 'male' ? 'Sakha' : 'Sakhi');
  const gender = friendProfile?.gender || 'female';
  const voiceId = getVoiceForGender(friendProfile?.gender);
  const alwaysSpeak = settings?.always_speak ?? true;

  // Preload character avatar images for seamless instant visual transitions
  useEffect(() => {
    const imagesToPreload = [
      '/characters/female_idle.jpg',
      '/characters/female_thinking.jpg',
      '/characters/female_speaking.jpg',
      '/characters/female_listening.jpg',
      '/characters/male_idle.jpg',
      '/characters/male_thinking.jpg',
      '/characters/male_speaking.jpg',
      '/characters/male_listening.jpg',
    ];
    imagesToPreload.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  }, []);

  // Show floating popup during AI speech if chat is open or user wants the floating popup experience (Requirement 8)
  useEffect(() => {
    if (isSpeaking) {
      setIsPopupVisible(true);
    } else {
      const timer = setTimeout(() => {
        setIsPopupVisible(false);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [isSpeaking]);

  // Handle incoming voice transcript from user
  const handleVoiceInput = async (spokenText: string) => {
    if (!spokenText.trim()) {
      setFriendState('idle');
      return;
    }

    setIsAiLoading(true);
    setFriendState('thinking');

    const tempUserMsg: Message = {
      id: Math.random().toString(),
      conversation_id: activeConversationId || 'temp',
      sender: 'user',
      content: spokenText,
      input_type: 'voice',
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await chatService.sendMessage(spokenText, activeConversationId, 'voice');
      setActiveConversationId(res.conversation_id);
      const displayText = res.display_text || res.reply;
      setCurrentAiReply(displayText);

      const assistantMsg: Message = {
        id: res.message_id,
        conversation_id: res.conversation_id,
        sender: 'assistant',
        content: displayText,
        input_type: 'text',
        created_at: new Date().toISOString(),
        searched: res.searched,
        sources: res.sources,
        search_timestamp: res.search_timestamp
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Speak response out loud through TTS with response_id deduplication and authoritative voice_id
      const targetVoiceId = res.voice_id || voiceId || getVoiceForGender(friendProfile?.gender);
      await speakResponse({
        response_id: res.response_id || res.message_id,
        speech_text: res.speech_text || '',
        voiceId: targetVoiceId
      });
    } catch (err: any) {
      setFriendState('error');
      toastError(err.response?.data?.detail || `Couldn't reach ${friendName}. Please try again.`);
    } finally {
      setIsAiLoading(false);
    }
  };

  // Handle typed message from Chat Panel
  const handleTextMessage = async (text: string) => {
    if (!text.trim()) return;

    setIsAiLoading(true);
    setFriendState('thinking');

    const tempUserMsg: Message = {
      id: Math.random().toString(),
      conversation_id: activeConversationId || 'temp',
      sender: 'user',
      content: text,
      input_type: 'text',
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await chatService.sendMessage(text, activeConversationId, 'text');
      setActiveConversationId(res.conversation_id);
      const displayText = res.display_text || res.reply;
      setCurrentAiReply(displayText);

      const assistantMsg: Message = {
        id: res.message_id,
        conversation_id: res.conversation_id,
        sender: 'assistant',
        content: displayText,
        input_type: 'text',
        created_at: new Date().toISOString(),
        searched: res.searched,
        sources: res.sources,
        search_timestamp: res.search_timestamp
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (alwaysSpeak) {
        const targetVoiceId = res.voice_id || voiceId || getVoiceForGender(friendProfile?.gender);
        await speakResponse({
          response_id: res.response_id || res.message_id,
          speech_text: res.speech_text || '',
          voiceId: targetVoiceId
        });
      } else {
        setFriendState('idle');
      }
    } catch (err: any) {
      setFriendState('error');
      toastError("Couldn't process message.");
    } finally {
      setIsAiLoading(false);
    }
  };

  // Mic Button Toggle
  const handleMicClick = () => {
    if (isSpeaking) {
      // Interruption support
      interrupt();
      startListening(handleVoiceInput);
      return;
    }

    if (isRecording) {
      stopListening();
    } else {
      startListening(handleVoiceInput);
    }
  };

  return (
    <div className="min-h-screen bg-[#070B14] text-white flex flex-col justify-between p-4 sm:p-6 select-none relative overflow-hidden">
      {/* 1. Deep Atmospheric Glows (Reference Screenshot Style) */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[650px] h-[650px] bg-purple-900/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-10 left-10 w-[450px] h-[450px] bg-pink-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[130px] pointer-events-none" />

      {/* 2. Top Header (Lotus Logo + Sakhi AI + Circular Action Buttons) */}
      <header className="flex items-center justify-between max-w-4xl mx-auto w-full z-20 pt-1">
        {/* Left: Lotus Icon + Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-pink-500/20 to-purple-600/20 border border-pink-500/30 flex items-center justify-center p-1.5 shadow-[0_0_15px_rgba(236,72,153,0.3)]">
            <img src="/lotus_icon.png" alt="Sakhi AI Logo" className="w-7 h-7 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-1.5">
                <span>Sakhi</span>
                <span className="bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">AI</span>
              </h1>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-400 font-medium">
              Your AI friend, always with you 💜
            </p>
          </div>
        </div>

        {/* Right: Settings & Profile Circular Glass Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => navigate('/settings')}
            aria-label="Settings"
            className="w-10 h-10 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-all shadow-md hover:border-pink-500/40"
          >
            <SettingsIcon className="w-4.5 h-4.5" />
          </button>

          <button
            onClick={() => navigate('/profile')}
            aria-label="User Profile"
            className="w-10 h-10 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white flex items-center justify-center transition-all shadow-md hover:border-purple-500/40 font-bold text-sm"
          >
            {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon className="w-4.5 h-4.5" />}
          </button>
        </div>
      </header>

      {/* 3. Main Center Area — Sakhi Character, Greeting Bubble & Glowing Mic */}
      <main className="flex-1 flex flex-col items-center justify-center text-center my-auto z-10 max-w-xl mx-auto w-full py-2">
        {/* Animated Character with Floating Greeting Bubble */}
        <div className="relative my-2">
          {/* Dynamic Greeting Bubble (Reference Screenshot Style) */}
          <div className="absolute -top-1 sm:-top-3 right-0 sm:-right-8 z-30 px-3.5 py-2 rounded-2xl rounded-bl-none bg-slate-900/90 border border-pink-500/40 backdrop-blur-xl shadow-[0_10px_25px_rgba(0,0,0,0.5)] animate-bounce [animation-duration:4s]">
            <p className="text-xs sm:text-sm font-semibold text-white flex items-center gap-1.5 whitespace-nowrap">
              <span>Hi {userName}!</span>
              <span className="text-pink-300">I'm here for you 💜</span>
            </p>
          </div>

          <AnimatedCharacter
            gender={gender}
            friendName={friendName}
            state={friendState}
            audioFrequency={audioFrequency}
            size="xl"
            onRetry={() => setFriendState('idle')}
          />
        </div>

        {/* Real-time Voice Transcript Bubble if speaking or transcribed */}
        {transcript && (
          <div className="my-2 px-4 py-2 rounded-2xl bg-purple-950/70 border border-purple-500/40 text-purple-200 text-xs sm:text-sm max-w-sm animate-scaleUp shadow-lg backdrop-blur-md">
            "{transcript}"
          </div>
        )}

        {/* Center Glowing Microphone Button with Stereo Waveform Flanks */}
        <div className="mt-4 mb-2">
          <MicrophoneButton
            isRecording={isRecording}
            isSpeaking={isSpeaking}
            friendState={friendState}
            audioFrequency={audioFrequency}
            onPress={handleMicClick}
            onStopSpeaking={stopSpeaking}
          />
        </div>

        <p className="text-xs text-slate-400 font-medium">
          {isSpeaking
            ? 'Speaking... Tap mic to interrupt'
            : isRecording
            ? 'Listening... Tap mic when done'
            : friendState === 'thinking'
            ? `${friendName} is thinking...`
            : 'Tap mic to talk in Telugu, English, or Tanglish'}
        </p>
      </main>

      {/* 4. Bottom Floating Pill Navigation Bar (Conversations, Memory, Settings) */}
      <footer className="flex items-center justify-center max-w-md mx-auto w-full z-20 pb-3">
        <div className="flex items-center gap-1 sm:gap-2 px-3 py-2 rounded-full bg-slate-900/85 border border-white/10 shadow-[0_15px_35px_rgba(0,0,0,0.6)] backdrop-blur-2xl">
          {/* Conversations Tab */}
          <button
            onClick={() => setIsChatOpen(true)}
            className="flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white px-4 py-2 rounded-full hover:bg-slate-800/80 transition-all"
          >
            <MessageSquare className="w-4 h-4 text-pink-400" />
            <span>Conversations</span>
          </button>

          <span className="w-px h-4 bg-slate-800" />

          {/* Memory Tab */}
          <button
            onClick={() => navigate('/memory')}
            className="flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white px-4 py-2 rounded-full hover:bg-slate-800/80 transition-all"
          >
            <Brain className="w-4 h-4 text-purple-400" />
            <span>Memory</span>
          </button>

          <span className="w-px h-4 bg-slate-800" />

          {/* Settings Tab */}
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white px-4 py-2 rounded-full hover:bg-slate-800/80 transition-all"
          >
            <SettingsIcon className="w-4 h-4 text-cyan-400" />
            <span>Settings</span>
          </button>
        </div>
      </footer>

      {/* 5. Floating Character Popup (Requirement 8) */}
      <CharacterPopup
        isOpen={isPopupVisible && isChatOpen}
        onClose={() => setIsPopupVisible(false)}
        friendName={friendName}
        gender={gender}
        state={friendState}
        audioFrequency={audioFrequency}
        currentSpeechText={currentAiReply}
        onStopSpeaking={stopSpeaking}
      />

      {/* 6. Sliding Chat Panel Drawer */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        messages={messages}
        onSendMessage={handleTextMessage}
        isLoading={isAiLoading}
        friendName={friendName}
        voiceId={voiceId}
        gender={gender}
      />
    </div>
  );
};
