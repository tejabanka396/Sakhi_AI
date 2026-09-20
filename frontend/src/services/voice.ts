import { api, API_BASE_URL } from './api';

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
  preview_supported?: boolean;
  sample_text?: string;
  // Backward compatibility
  id?: string;
  name?: string;
  label?: string;
  language?: string;
  description?: string;
  underlying_model?: string;
  model_notes?: string;
}

/**
 * Centralized gender-to-voice mapping
 * female / Female / FEMALE -> female_voice
 * male / Male / MALE -> male_voice
 * missing/invalid -> female_voice
 */
export function getVoiceForGender(gender?: string): string {
  const g = (gender || '').toLowerCase().trim();
  if (g === 'male') {
    return 'male_voice';
  }
  return 'female_voice';
}

/**
 * Centralized clean user-facing voice label
 * Displays "Male Voice" or "Female Voice", never exposing legacy technical IDs
 */
export function getVoiceLabel(genderOrVoiceId?: string): string {
  const val = (genderOrVoiceId || '').toLowerCase().trim();
  if (val === 'male' || val === 'male_voice' || val.startsWith('male_')) {
    return 'Male Voice';
  }
  return 'Female Voice';
}

/**
 * Centralized voice description
 */
export function getVoiceDescription(genderOrVoiceId?: string): string {
  const val = (genderOrVoiceId || '').toLowerCase().trim();
  if (val === 'male' || val === 'male_voice' || val.startsWith('male_')) {
    return 'Natural Telugu male voice';
  }
  return 'Natural Telugu female voice';
}

export const voiceService = {
  async getVoiceOptions(): Promise<VoiceOption[]> {
    const res = await api.get<{ voices: VoiceOption[] }>('/api/voice/options');
    return res.data.voices;
  },

  async synthesize(text: string, voiceId: string = 'female_voice', language: string = 'auto'): Promise<Blob> {
    const res = await api.post('/api/voice/synthesize', {
      text,
      voice_id: voiceId,
      language
    }, {
      responseType: 'blob'
    });
    return res.data;
  },

  getPreviewUrl(voiceId: string): string {
    return `${API_BASE_URL}/api/voice/preview/${voiceId}`;
  },

  async transcribe(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'speech.webm');
    const res = await api.post<{ transcript: string; language: string }>('/api/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data.transcript;
  }
};
