import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Phone, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, requestPhoneOtp, verifyPhoneOtp } = useAuth();
  const { success, error: toastError } = useToast();

  const [authMethod, setAuthMethod] = useState<'email' | 'phone'>('email');

  // Email form
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Phone form
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpRequested, setOtpRequested] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const [isLoading, setIsLoading] = useState(false);

  // Resend OTP countdown timer
  React.useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setIsLoading(true);
    try {
      const res = await login(email, password);
      success('Logged in successfully ❤️');
      if (res.onboarding_completed) {
        navigate('/home');
      } else {
        navigate('/onboarding');
      }
    } catch (err: any) {
      toastError(err.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanDigits = phone.replace(/\D/g, '');
    let core = cleanDigits;
    if (cleanDigits.length === 11 && cleanDigits.startsWith('0')) core = cleanDigits.slice(1);
    else if (cleanDigits.length === 12 && cleanDigits.startsWith('91')) core = cleanDigits.slice(2);

    if (core.length !== 10 || !/^[6-9]\d{9}$/.test(core)) {
      toastError('Please enter a valid 10-digit Indian mobile number (starts with 6-9).');
      return;
    }

    setIsLoading(true);
    try {
      const res = await requestPhoneOtp(phone);
      setOtpRequested(true);
      setOtp('');
      setCountdown(60);
      success(res.message || 'OTP sent successfully! Please check your SMS messages.');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        toastError(detail);
      } else {
        toastError('Could not send OTP. Please check your number and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanOtp = otp.trim();
    if (cleanOtp.length !== 6 || !/^\d{6}$/.test(cleanOtp)) {
      toastError('Please enter a valid 6-digit numeric OTP.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await verifyPhoneOtp(phone, cleanOtp);
      success('Phone verified successfully! Welcome ❤️');
      if (res.onboarding_completed) {
        navigate('/home');
      } else {
        navigate('/onboarding');
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Invalid OTP code.';
      toastError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-4 sm:p-6 select-none relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96 bg-rose-500/15 rounded-full blur-3xl pointer-events-none" />

      {/* Card */}
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800/90 p-8 rounded-3xl shadow-2xl backdrop-blur-2xl z-10 animate-scaleUp">
        {/* Brand */}
        <div className="flex flex-col items-center text-center mb-7">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-rose-500 to-purple-600 flex items-center justify-center text-white font-bold text-2xl shadow-xl shadow-rose-950/50 mb-3">
            S
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Sakhi AI</h2>
          <p className="text-slate-300 text-sm mt-1">Good to see you again ❤️</p>
        </div>

        {/* Method Switcher */}
        <div className="grid grid-cols-2 p-1 rounded-xl bg-slate-800/80 border border-slate-700/60 mb-6">
          <button
            type="button"
            onClick={() => {
              setAuthMethod('email');
              setOtpRequested(false);
            }}
            className={`py-2 text-xs font-semibold rounded-lg transition-all ${
              authMethod === 'email'
                ? 'bg-rose-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Email
          </button>
          <button
            type="button"
            onClick={() => setAuthMethod('phone')}
            className={`py-2 text-xs font-semibold rounded-lg transition-all ${
              authMethod === 'phone'
                ? 'bg-rose-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Phone OTP
          </button>
        </div>

        {/* Email Login Form */}
        {authMethod === 'email' && (
          <form onSubmit={handleEmailLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Email address</label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 hover:opacity-95 text-white font-semibold text-sm shadow-lg shadow-rose-950/50 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        )}

        {/* Phone OTP Login Form */}
        {authMethod === 'phone' && (
          <div className="space-y-4">
            {!otpRequested ? (
              <form onSubmit={handleRequestOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Mobile Number</label>
                  <div className="relative">
                    <div className="absolute left-3.5 top-1/2 -translate-y-1/2 flex items-center gap-1 text-slate-400 text-sm font-medium">
                      <span>🇮🇳 +91</span>
                    </div>
                    <input
                      type="tel"
                      required
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="9876543210"
                      className="w-full pl-24 pr-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1.5">
                    We will send a 6-digit verification code to your phone number.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !phone}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 hover:opacity-95 text-white font-semibold text-sm shadow-lg shadow-rose-950/50 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? 'Sending SMS OTP...' : 'Send SMS OTP'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-4 animate-fadeIn">
                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-center">
                  <p className="text-xs text-rose-300">
                    OTP sent to <span className="font-semibold text-white">+91 {phone}</span>
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-slate-300">Enter 6-digit OTP</label>
                    <button
                      type="button"
                      onClick={() => {
                        setOtpRequested(false);
                        setOtp('');
                      }}
                      className="text-xs text-rose-400 hover:underline"
                    >
                      Change phone
                    </button>
                  </div>
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    autoFocus
                    required
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="••••••"
                    className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-center text-xl tracking-[0.3em] font-mono focus:outline-none focus:ring-2 focus:ring-rose-500/50"
                  />
                  <div className="flex items-center justify-between mt-2.5">
                    <span className="text-[11px] text-slate-400">Didn't receive SMS?</span>
                    {countdown > 0 ? (
                      <span className="text-[11px] text-slate-400 font-mono">Resend in {countdown}s</span>
                    ) : (
                      <button
                        type="button"
                        disabled={isLoading}
                        onClick={handleRequestOtp}
                        className="text-[11px] text-rose-400 hover:text-rose-300 hover:underline font-medium"
                      >
                        Resend SMS OTP
                      </button>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !otp}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 hover:opacity-95 text-white font-semibold text-sm shadow-lg shadow-rose-950/50 disabled:opacity-50 transition-all"
                >
                  {isLoading ? 'Verifying...' : 'Verify and Sign In'}
                </button>
              </form>
            )}
          </div>
        )}

        {/* Link to Register */}
        <div className="mt-6 text-center text-xs text-slate-400">
          New to Sakhi AI?{' '}
          <Link to="/register" className="text-rose-400 hover:text-rose-300 font-semibold underline">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
};
