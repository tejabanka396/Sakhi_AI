import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import { FriendState } from '../types';
import { voiceService } from '../services/voice';
import { audioManager, PlaybackState } from '../services/audioManager';
import { useToast } from './ToastContext';

export interface SpeakOptions {
  responseId?: string;
  response_id?: string;
  messageId?: string;
  message_id?: string;
  text?: string;
  speech_text?: string;
  voiceId?: string;
  voice_id?: string;
  language?: string;
}

interface VoiceContextType {
  friendState: FriendState;
  setFriendState: (state: FriendState) => void;
  isRecording: boolean;
  isSpeaking: boolean;
  audioFrequency: number;
  transcript: string;
  startListening: (onFinalTranscript?: (text: string) => void) => Promise<void>;
  stopListening: () => void;
  speakResponse: (textOrPayload: string | SpeakOptions, voiceId?: string) => Promise<void>;
  previewVoice: (voiceId: string) => Promise<void>;
  stopSpeaking: () => void;
  interrupt: () => void;
  micPermissionDenied: boolean;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export const VoiceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [friendState, setFriendState] = useState<FriendState>('idle');
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [audioFrequency, setAudioFrequency] = useState<number>(0);
  const [transcript, setTranscript] = useState<string>('');
  const [micPermissionDenied, setMicPermissionDenied] = useState<boolean>(false);

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const { error: toastError } = useToast();

  // 1. Subscribe directly to Centralized AudioManager
  useEffect(() => {
    const unsubscribe = audioManager.subscribe((playbackState: PlaybackState, frequency: number) => {
      setAudioFrequency(frequency);

      if (playbackState === 'PLAYING') {
        setIsSpeaking(true);
        setFriendState('speaking');
      } else if (playbackState === 'IDLE') {
        setIsSpeaking(false);
        setFriendState((prev) => (prev === 'speaking' ? 'idle' : prev));
      } else if (playbackState === 'ERROR') {
        setIsSpeaking(false);
        setFriendState((prev) => (prev === 'speaking' ? 'idle' : prev));
      }
    });

    return () => {
      unsubscribe();
      audioManager.stop();
      stopListening();
    };
  }, []);

  const stopSpeaking = useCallback(() => {
    audioManager.stop();
    setIsSpeaking(false);
    setAudioFrequency(0);
    setFriendState((prev) => (prev === 'speaking' ? 'idle' : prev));
  }, []);

  const interrupt = useCallback(() => {
    audioManager.interrupt();
    setIsSpeaking(false);
    setAudioFrequency(0);
    setFriendState('listening');
  }, []);

  /**
   * Central speak entry point:
   * Accepts either an options object with stable response_id or legacy (text, voiceId) arguments.
   * Enforces deduplication through AudioManager.
   */
  const speakResponse = useCallback(
    async (textOrPayload: string | SpeakOptions, optionalVoiceId?: string) => {
      let responseId = '';
      let speechText = '';
      let voiceId = optionalVoiceId || 'female_voice';
      let language = 'auto';

      if (typeof textOrPayload === 'string') {
        speechText = textOrPayload;
        // Generate stable content hash for string inputs without explicit ID
        responseId = `msg_${hashString(speechText)}`;
      } else if (textOrPayload && typeof textOrPayload === 'object') {
        responseId =
          textOrPayload.responseId ||
          textOrPayload.response_id ||
          textOrPayload.messageId ||
          textOrPayload.message_id ||
          `msg_${hashString(textOrPayload.speech_text || textOrPayload.text || '')}`;
        speechText = textOrPayload.speech_text || textOrPayload.text || '';
        voiceId = textOrPayload.voiceId || textOrPayload.voice_id || optionalVoiceId || 'female_voice';
        language = textOrPayload.language || 'auto';
      }

      if (!speechText || !speechText.trim()) {
        return;
      }

      await audioManager.speak(responseId, speechText, voiceId, language);
    },
    []
  );

  /**
   * Preview a voice option using the Central AudioManager.
   */
  const previewVoice = useCallback(async (voiceId: string) => {
    await audioManager.previewVoice(voiceId);
  }, []);

  // 2. Speech-to-Text Listening Logic
  const startListening = useCallback(
    async (onFinalTranscript?: (text: string) => void) => {
      // If speaking, interrupt!
      if (audioManager.isSpeaking() || isSpeaking) {
        interrupt();
      }

      setTranscript('');
      setIsRecording(true);
      setFriendState('listening');

      // Check for Web Speech Recognition API
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognitionRef.current = recognition;
          recognition.continuous = false;
          recognition.interimResults = true;
          recognition.lang = 'te-IN'; // Default to Telugu with auto adaptation

          recognition.onresult = (event: any) => {
            let currentTranscript = '';
            for (let i = 0; i < event.results.length; i++) {
              currentTranscript += event.results[i][0].transcript;
            }
            setTranscript(currentTranscript);

            if (event.results[0].isFinal) {
              setIsRecording(false);
              setFriendState('thinking');
              if (onFinalTranscript) {
                onFinalTranscript(currentTranscript);
              }
            }
          };

          recognition.onerror = async (event: any) => {
            console.warn('SpeechRecognition error:', event.error);
            if (event.error === 'not-allowed') {
              setMicPermissionDenied(true);
              toastError('Microphone permission denied. You can still type your message in Chat mode!');
              setIsRecording(false);
              setFriendState('idle');
            } else {
              startMediaRecorderFallback(onFinalTranscript);
            }
          };

          recognition.onend = () => {
            setIsRecording(false);
          };

          recognition.start();
          return;
        } catch (e) {
          console.warn('SpeechRecognition init error, falling back to MediaRecorder:', e);
        }
      }

      // MediaRecorder Fallback
      startMediaRecorderFallback(onFinalTranscript);
    },
    [isSpeaking, interrupt, toastError]
  );

  const startMediaRecorderFallback = async (onFinalTranscript?: (text: string) => void) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        setFriendState('thinking');
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const transcribedText = await voiceService.transcribe(audioBlob);
          if (transcribedText && onFinalTranscript) {
            onFinalTranscript(transcribedText);
          } else {
            setFriendState('idle');
          }
        } catch {
          setFriendState('error');
          toastError("Couldn't process voice recording. Try typing or speaking again.");
        }
      };

      mediaRecorder.start();
    } catch (err: any) {
      console.error('Microphone access denied:', err);
      setMicPermissionDenied(true);
      setIsRecording(false);
      setFriendState('idle');
      toastError('Microphone access blocked. Please enable it in browser settings.');
    }
  };

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore
      }
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        // Ignore
      }
      mediaRecorderRef.current = null;
    }

    setIsRecording(false);
  }, []);

  return (
    <VoiceContext.Provider
      value={{
        friendState,
        setFriendState,
        isRecording,
        isSpeaking,
        audioFrequency,
        transcript,
        startListening,
        stopListening,
        speakResponse,
        previewVoice,
        stopSpeaking,
        interrupt,
        micPermissionDenied,
      }}
    >
      {children}
    </VoiceContext.Provider>
  );
};

export const useVoice = () => {
  const context = useContext(VoiceContext);
  if (!context) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
};

// Helper: Stable string hash for duplicate prevention
function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}
