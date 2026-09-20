import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Search, MessageSquare, Trash2, Edit2, Clock, Sparkles } from 'lucide-react';
import { conversationsService, ConversationDetail } from '../services/conversations';
import { Conversation } from '../types';
import { useToast } from '../context/ToastContext';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';

export const Conversations: React.FC = () => {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Rename modal state
  const [renamingConv, setRenamingConv] = useState<Conversation | null>(null);
  const [newTitle, setNewTitle] = useState('');

  // Delete modal state
  const [deletingConv, setDeletingConv] = useState<Conversation | null>(null);

  // View detail modal state
  const [viewingConv, setViewingConv] = useState<ConversationDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const data = await conversationsService.list();
      setConversations(data);
    } catch {
      toastError('Could not load conversations.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  const handleOpenRename = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setRenamingConv(conv);
    setNewTitle(conv.title);
  };

  const handleSaveRename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renamingConv || !newTitle.trim()) return;
    try {
      await conversationsService.rename(renamingConv.id, newTitle.trim());
      success('Conversation renamed ✓');
      setRenamingConv(null);
      loadConversations();
    } catch {
      toastError('Could not rename conversation.');
    }
  };

  const handleOpenDelete = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingConv(conv);
  };

  const handleConfirmDelete = async () => {
    if (!deletingConv) return;
    try {
      await conversationsService.delete(deletingConv.id);
      success('Conversation deleted permanently ✓');
      setDeletingConv(null);
      loadConversations();
    } catch {
      toastError('Failed to delete conversation.');
    }
  };

  const handleSelectConversation = async (conv: Conversation) => {
    setIsLoadingDetail(true);
    try {
      const detail = await conversationsService.getDetail(conv.id);
      setViewingConv(detail);
    } catch {
      toastError('Failed to load conversation details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.last_message && c.last_message.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-4 sm:p-8 select-none relative">
      <div className="max-w-3xl mx-auto">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/home')}
            aria-label="Back to home"
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all flex items-center gap-2 text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Home</span>
          </button>
          <h1 className="text-xl font-bold tracking-tight text-white">Conversations</h1>
          <div className="w-16" /> {/* Balance spacer */}
        </div>

        {/* Search Input */}
        <div className="relative mb-6">
          <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations by title or topic..."
            className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/40 shadow-md"
          />
        </div>

        {/* Conversation List */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 rounded-2xl bg-slate-900/60 border border-slate-800/80 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
            <Sparkles className="w-12 h-12 text-rose-400/50 mb-3" />
            <h3 className="text-lg font-semibold text-slate-200">No conversations found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Tap the microphone or type on the home screen to have your first conversation with Sakhi!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((conv) => (
              <div
                key={conv.id}
                onClick={() => handleSelectConversation(conv)}
                className="group cursor-pointer p-5 rounded-2xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800/80 hover:border-slate-700 transition-all duration-200 shadow-md flex items-start justify-between gap-4"
              >
                <div className="flex items-start gap-3.5 flex-1 min-w-0">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-500/20 to-purple-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0 mt-0.5">
                    <MessageSquare className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-base text-white truncate">{conv.title}</h3>
                      {conv.message_count !== undefined && conv.message_count > 0 && (
                        <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[11px] text-slate-400 font-medium">
                          {conv.message_count} {conv.message_count === 1 ? 'msg' : 'msgs'}
                        </span>
                      )}
                    </div>
                    {conv.last_message && (
                      <p className="text-sm text-slate-400 truncate mt-1">{conv.last_message}</p>
                    )}
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-2">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(conv.updated_at || conv.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleOpenRename(conv, e)}
                    aria-label="Rename conversation"
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleOpenDelete(conv, e)}
                    aria-label="Delete conversation"
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Rename Modal */}
      <Modal
        isOpen={!!renamingConv}
        onClose={() => setRenamingConv(null)}
        title="Rename conversation"
        maxWidth="sm"
      >
        <form onSubmit={handleSaveRename} className="space-y-4">
          <input
            type="text"
            required
            autoFocus
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50"
          />
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setRenamingConv(null)}
              className="px-4 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-500 to-purple-600 text-white text-sm font-semibold hover:opacity-95 shadow-md transition-all"
            >
              Save
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={!!deletingConv}
        onClose={() => setDeletingConv(null)}
        onConfirm={handleConfirmDelete}
        title="Delete this conversation?"
        message="This conversation will be permanently removed from your history along with all its messages."
        confirmText="Delete"
        isDestructive={true}
      />

      {/* Detail Modal */}
      <Modal
        isOpen={!!viewingConv}
        onClose={() => setViewingConv(null)}
        title={viewingConv?.title || 'Conversation Detail'}
        maxWidth="lg"
      >
        <div className="max-h-[60vh] overflow-y-auto space-y-3 p-1">
          {viewingConv?.messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm ${
                  m.sender === 'user'
                    ? 'bg-gradient-to-r from-rose-500 to-purple-600 text-white'
                    : 'bg-slate-800 border border-slate-700 text-slate-200'
                }`}
              >
                {m.content}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 px-1">
                {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
};
