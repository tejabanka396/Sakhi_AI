import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Heart, Trash2, Plus, Sparkles, Tag, ShieldCheck } from 'lucide-react';
import { memoryService } from '../services/memory';
import { Memory } from '../types';
import { useToast } from '../context/ToastContext';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';

export const MemoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Add memory modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [newCategory, setNewCategory] = useState<'preference' | 'learning' | 'goal' | 'personal'>('preference');

  // Delete modal state
  const [deletingMemory, setDeletingMemory] = useState<Memory | null>(null);
  const [isClearAllOpen, setIsClearAllOpen] = useState(false);

  const loadMemories = async () => {
    setIsLoading(true);
    try {
      const data = await memoryService.list();
      setMemories(data);
    } catch {
      toastError('Could not load memories.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;
    try {
      await memoryService.add(newMemoryText.trim(), newCategory);
      success('Memory remembered ✓');
      setIsAddOpen(false);
      setNewMemoryText('');
      loadMemories();
    } catch {
      toastError('Failed to save memory.');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingMemory) return;
    try {
      await memoryService.delete(deletingMemory.id);
      success('Memory forgotten ✓');
      setDeletingMemory(null);
      loadMemories();
    } catch {
      toastError('Could not delete memory.');
    }
  };

  const handleConfirmClearAll = async () => {
    try {
      await memoryService.clearAll();
      success('All memories cleared ✓');
      setIsClearAllOpen(false);
      loadMemories();
    } catch {
      toastError('Could not clear memories.');
    }
  };

  const categoryBadges: Record<string, { label: string; color: string }> = {
    preference: { label: 'Preference', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
    learning: { label: 'Learning Goal', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' },
    goal: { label: 'Target / Goal', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
    personal: { label: 'Personal Fact', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-4 sm:p-8 select-none relative">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/home')}
            aria-label="Back to home"
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all flex items-center gap-2 text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Home</span>
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsAddOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 hover:opacity-95 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md"
            >
              <Plus className="w-4 h-4" />
              <span>Add fact</span>
            </button>
            {memories.length > 0 && (
              <button
                onClick={() => setIsClearAllOpen(true)}
                className="px-3 py-2 rounded-xl border border-rose-900/60 hover:bg-rose-950/40 text-rose-300 text-xs font-medium transition-colors"
              >
                Clear all
              </button>
            )}
          </div>
        </div>

        {/* Title and Explanation */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/30 text-rose-400 mb-3 shadow-lg">
            <Heart className="w-6 h-6 fill-current" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">What Sakhi Remembers</h1>
          <p className="text-slate-400 text-sm max-w-md mx-auto mt-1 leading-relaxed">
            Sakhi automatically remembers important subjects, preferences, and goals you share so every conversation feels personal.
          </p>
        </div>

        {/* Memory Cards */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse" />
            ))}
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400 bg-slate-900/40 border border-slate-800/80 rounded-3xl p-8">
            <Sparkles className="w-10 h-10 text-rose-400/60 mb-3" />
            <h3 className="text-base font-semibold text-slate-200">No memories stored yet</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-xs leading-relaxed">
              When you tell Sakhi "I want to learn Python" or "My favorite subject is DBMS", it will remember it here!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((m) => {
              const badge = categoryBadges[m.category] || categoryBadges.preference;
              return (
                <div
                  key={m.id}
                  className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-all shadow-md flex items-start justify-between gap-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${badge.color}`}>
                        {badge.label}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(m.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-100 leading-relaxed">
                      "{m.memory_text}"
                    </p>
                  </div>

                  <button
                    onClick={() => setDeletingMemory(m)}
                    aria-label="Forget memory"
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-xl transition-colors shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Security & Privacy Notice */}
        <div className="mt-8 p-4 rounded-2xl bg-slate-900/50 border border-slate-800/60 flex items-center gap-3 text-xs text-slate-400">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>
            Passwords, keys, and temporary remarks are never saved. You have 100% control to view or forget any memory at any time.
          </span>
        </div>
      </div>

      {/* Add Memory Modal */}
      <Modal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        title="Tell Sakhi something to remember"
        maxWidth="sm"
      >
        <form onSubmit={handleAddMemory} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">What should Sakhi remember?</label>
            <textarea
              required
              rows={3}
              value={newMemoryText}
              onChange={(e) => setNewMemoryText(e.target.value)}
              placeholder="e.g. My favorite subject is operating systems and I love building web apps."
              className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Category</label>
            <select
              value={newCategory}
              onChange={(e: any) => setNewCategory(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
            >
              <option value="preference">Preference</option>
              <option value="learning">Learning Goal</option>
              <option value="goal">Target / Dream</option>
              <option value="personal">Personal Fact</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setIsAddOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-sm hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 text-white text-sm font-semibold hover:opacity-95 shadow-md"
            >
              Remember
            </button>
          </div>
        </form>
      </Modal>

      {/* Forget Single Memory Modal */}
      <ConfirmDialog
        isOpen={!!deletingMemory}
        onClose={() => setDeletingMemory(null)}
        onConfirm={handleConfirmDelete}
        title="Forget this memory?"
        message={`Sakhi will no longer remember: "${deletingMemory?.memory_text}"`}
        confirmText="Forget"
        cancelText="Keep it"
        isDestructive={true}
      />

      {/* Clear All Memories Modal */}
      <ConfirmDialog
        isOpen={isClearAllOpen}
        onClose={() => setIsClearAllOpen(false)}
        onConfirm={handleConfirmClearAll}
        title="Clear all memories?"
        message="Are you sure? Sakhi will no longer remember any of your saved preferences or goals."
        confirmText="Clear All"
        cancelText="Cancel"
        isDestructive={true}
      />
    </div>
  );
};
