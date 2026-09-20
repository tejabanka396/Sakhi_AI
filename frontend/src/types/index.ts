export type Gender = 'female' | 'male';

export type ConversationMode = 'talk' | 'chat' | 'auto';

export type LanguagePreference = 'auto' | 'telugu' | 'english';

export type FriendState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'happy' | 'laughing' | 'error';

export type MessageSender = 'user' | 'assistant';

export type MessageInputType = 'voice' | 'text';

export type MemoryCategory = 'preference' | 'learning' | 'goal' | 'personal';

export interface User {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  auth_provider: string;
  created_at: string;
  updated_at?: string;
  onboarding_completed?: boolean;
}

export interface FriendProfile {
  id: string;
  user_id: string;
  friend_name: string;
  gender: Gender;
  voice_id: string;
  personality: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  default_mode: ConversationMode;
  voice_enabled: boolean;
  always_speak: boolean;
  language_preference: LanguagePreference;
  created_at?: string;
  updated_at?: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: MessageSender;
  content: string;
  input_type: MessageInputType;
  created_at: string;
}

export interface Memory {
  id: string;
  user_id: string;
  memory_text: string;
  category: MemoryCategory;
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  onboarding_completed?: boolean;
  user: User;
  friend_profile?: FriendProfile | null;
  settings?: UserSettings | null;
}

export interface ChatResponse {
  reply: string;
  display_text?: string;
  speech_text?: string;
  conversation_id: string;
  message_id: string;
  response_id?: string;
  voice_id?: string;
  gender?: string;
  sender: 'assistant';
  audio_base64?: string | null;
  audio_url?: string | null;
}

export interface VoiceOption {
  voice_id: string;
  display_name: string;
  gender: string;
  style: string;
  personality: string;
  dialect?: string;
  provider: string;
  provider_voice: string;
  exact_underlying_voice?: string;
  is_acoustically_independent?: boolean;
  prosody_changes?: string;
  dialect_layer?: string;
  preview_supported: boolean;
  sample_text?: string;
  // Backward compatibility
  id?: string;
  name?: string;
  label?: string;
  language?: string;
  sampleText?: string;
  description?: string;
  underlying_model?: string;
  model_notes?: string;
  edgeVoiceName?: string;
}
