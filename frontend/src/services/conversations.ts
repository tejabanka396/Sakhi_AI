import { api } from './api';
import { Conversation, Message } from '../types';

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export const conversationsService = {
  async list(): Promise<Conversation[]> {
    const res = await api.get<Conversation[]>('/api/conversations');
    return res.data;
  },

  async getDetail(id: string): Promise<ConversationDetail> {
    const res = await api.get<ConversationDetail>(`/api/conversations/${id}`);
    return res.data;
  },

  async rename(id: string, title: string): Promise<Conversation> {
    const res = await api.put<Conversation>(`/api/conversations/${id}`, { title });
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/conversations/${id}`);
  }
};
