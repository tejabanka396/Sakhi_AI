import { api } from './api';
import { Memory } from '../types';

export const memoryService = {
  async list(): Promise<Memory[]> {
    const res = await api.get<Memory[]>('/api/memories');
    return res.data;
  },

  async add(memoryText: string, category: string = 'preference'): Promise<Memory> {
    const res = await api.post<Memory>('/api/memories', {
      memory_text: memoryText,
      category
    });
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/memories/${id}`);
  },

  async clearAll(): Promise<void> {
    await api.delete('/api/memories');
  }
};
