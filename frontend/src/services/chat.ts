import { api } from './api';
import { ChatResponse } from '../types';

export const chatService = {
  async sendMessage(message: string, conversationId?: string, inputType: 'text' | 'voice' = 'text'): Promise<ChatResponse> {
    const res = await api.post<ChatResponse>('/api/chat', {
      message,
      conversation_id: conversationId,
      input_type: inputType,
    });
    return res.data;
  },
};
