import { api } from './api';
import { AuthResponse, User, FriendProfile, UserSettings } from '../types';

export const authService = {
  async register(data: { name: string; email: string; password: string; phone?: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/api/auth/register', data);
    return res.data;
  },

  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/api/auth/login', data);
    return res.data;
  },

  async googleAuth(data: { token?: string; email?: string; name?: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/api/auth/google', data);
    return res.data;
  },

  async requestPhoneOtp(phone: string): Promise<{ success: boolean; message: string }> {
    const res = await api.post('/api/auth/phone/request-otp', { phone });
    return res.data;
  },

  async verifyPhoneOtp(data: { phone: string; otp: string; name?: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/api/auth/phone/verify-otp', data);
    return res.data;
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('sakhi_refresh_token');
    try {
      await api.post('/api/auth/logout', { refresh_token: refreshToken });
    } finally {
      localStorage.removeItem('sakhi_access_token');
      localStorage.removeItem('sakhi_refresh_token');
      localStorage.removeItem('sakhi_user');
      localStorage.removeItem('sakhi_friend');
      localStorage.removeItem('sakhi_settings');
    }
  },

  async getMe(): Promise<User> {
    const res = await api.get<User>('/api/users/me');
    return res.data;
  },

  async updateMe(data: Partial<User>): Promise<User> {
    const res = await api.put<User>('/api/users/me', data);
    return res.data;
  },

  async deleteAccount(): Promise<void> {
    await api.delete('/api/users/me');
    localStorage.clear();
  },

  async getFriendProfile(): Promise<FriendProfile> {
    const res = await api.get<FriendProfile>('/api/friend/profile');
    return res.data;
  },

  async updateFriendProfile(data: Partial<FriendProfile>): Promise<FriendProfile> {
    const res = await api.put<FriendProfile>('/api/friend/profile', data);
    return res.data;
  },

  async getSettings(): Promise<UserSettings> {
    const res = await api.get<UserSettings>('/api/friend/settings');
    return res.data;
  },

  async updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
    const res = await api.put<UserSettings>('/api/friend/settings', data);
    return res.data;
  }
};
