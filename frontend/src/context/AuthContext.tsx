import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, FriendProfile, UserSettings, AuthResponse } from '../types';
import { authService } from '../services/auth';

interface AuthContextType {
  user: User | null;
  friendProfile: FriendProfile | null;
  settings: UserSettings | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  onboardingCompleted: boolean;
  login: (email: string, pass: string) => Promise<AuthResponse>;
  register: (name: string, email: string, pass: string, phone?: string) => Promise<AuthResponse>;
  loginGoogle: (token?: string, email?: string, name?: string) => Promise<AuthResponse>;
  requestPhoneOtp: (phone: string) => Promise<{ success: boolean; message: string }>;
  verifyPhoneOtp: (phone: string, otp: string, name?: string) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  updateFriendProfile: (data: Partial<FriendProfile>) => Promise<void>;
  updateSettings: (data: Partial<UserSettings>) => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  deleteAccount: () => Promise<void>;
  setOnboardingCompleted: (val: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('sakhi_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [friendProfile, setFriendProfile] = useState<FriendProfile | null>(() => {
    const saved = localStorage.getItem('sakhi_friend');
    return saved ? JSON.parse(saved) : null;
  });

  const [settings, setSettings] = useState<UserSettings | null>(() => {
    const saved = localStorage.getItem('sakhi_settings');
    return saved ? JSON.parse(saved) : null;
  });

  const [token, setToken] = useState<string | null>(() => localStorage.getItem('sakhi_access_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [onboardingCompleted, setOnboardingCompletedState] = useState<boolean>(() => {
    return localStorage.getItem('sakhi_onboarding_done') === 'true';
  });

  const setOnboardingCompleted = (val: boolean) => {
    setOnboardingCompletedState(val);
    localStorage.setItem('sakhi_onboarding_done', val ? 'true' : 'false');
  };

  const handleAuthSuccess = (data: AuthResponse) => {
    localStorage.setItem('sakhi_access_token', data.access_token);
    localStorage.setItem('sakhi_refresh_token', data.refresh_token);
    localStorage.setItem('sakhi_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);

    if (data.friend_profile) {
      localStorage.setItem('sakhi_friend', JSON.stringify(data.friend_profile));
      setFriendProfile(data.friend_profile);
    }
    if (data.settings) {
      localStorage.setItem('sakhi_settings', JSON.stringify(data.settings));
      setSettings(data.settings);
    }

    const isDone = data.onboarding_completed ?? false;
    setOnboardingCompleted(isDone);
  };

  const login = async (email: string, pass: string): Promise<AuthResponse> => {
    const data = await authService.login({ email, password: pass });
    handleAuthSuccess(data);
    return data;
  };

  const register = async (name: string, email: string, pass: string, phone?: string): Promise<AuthResponse> => {
    const data = await authService.register({ name, email, password: pass, phone });
    handleAuthSuccess(data);
    return data;
  };

  const loginGoogle = async (tok?: string, email?: string, name?: string): Promise<AuthResponse> => {
    const data = await authService.googleAuth({ token: tok, email, name });
    handleAuthSuccess(data);
    return data;
  };

  const requestPhoneOtp = async (phone: string) => {
    return await authService.requestPhoneOtp(phone);
  };

  const verifyPhoneOtp = async (phone: string, otp: string, name?: string): Promise<AuthResponse> => {
    const data = await authService.verifyPhoneOtp({ phone, otp, name });
    handleAuthSuccess(data);
    return data;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch {
      // ignore network issue on logout
    } finally {
      setUser(null);
      setFriendProfile(null);
      setSettings(null);
      setToken(null);
      setOnboardingCompletedState(false);
      localStorage.clear();
    }
  };

  const updateFriendProfile = async (data: Partial<FriendProfile>) => {
    const updated = await authService.updateFriendProfile(data);
    setFriendProfile(updated);
    localStorage.setItem('sakhi_friend', JSON.stringify(updated));
  };

  const updateSettings = async (data: Partial<UserSettings>) => {
    const updated = await authService.updateSettings(data);
    setSettings(updated);
    localStorage.setItem('sakhi_settings', JSON.stringify(updated));
  };

  const updateUser = async (data: Partial<User>) => {
    const updated = await authService.updateMe(data);
    setUser(updated);
    localStorage.setItem('sakhi_user', JSON.stringify(updated));
  };

  const deleteAccount = async () => {
    try {
      await authService.deleteAccount();
    } catch {
      // ignore
    } finally {
      setUser(null);
      setFriendProfile(null);
      setSettings(null);
      setToken(null);
      setOnboardingCompletedState(false);
      localStorage.clear();
    }
  };

  // Sync profile & settings on mount if authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem('sakhi_access_token');
      if (savedToken) {
        try {
          const [userData, friendData, settingsData] = await Promise.all([
            authService.getMe(),
            authService.getFriendProfile(),
            authService.getSettings()
          ]);
          setUser(userData);
          setFriendProfile(friendData);
          setSettings(settingsData);
          if (userData.onboarding_completed) {
            setOnboardingCompleted(true);
          }
        } catch {
          // Token expired or invalid
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        friendProfile,
        settings,
        token,
        isAuthenticated: !!user,
        isLoading,
        onboardingCompleted,
        login,
        register,
        loginGoogle,
        requestPhoneOtp,
        verifyPhoneOtp,
        logout,
        updateFriendProfile,
        updateSettings,
        updateUser,
        deleteAccount,
        setOnboardingCompleted
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
