import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios from 'axios';
import { 
  Plus, 
  Upload, 
  FileText, 
  MessageSquare, 
  Send, 
  CheckCircle2, 
  Loader2, 
  RefreshCcw,
  Search,
  BookOpen,
  FolderPlus,
  Folder,
  Trash2,
  Layers,
  ArrowLeft,
  CheckSquare,
  Square,
  Edit2,
  Circle,
  CheckCircle,
  Library,
  Files,
  ChevronDown,
  ArrowRight,
  Link as LinkIcon,
  Clock,
  MoreVertical,
  Pin,
  PinOff,
  X,
  Zap,
  Maximize2,
  Minimize2
} from 'lucide-react';
import api from '../services/api';
import { useNotifications } from '../context/NotificationContext';

// --- TYPES ---
interface Project {
  id: string;
  name: string;
  description: string | null;
  documents: Document[];
}

interface Document {
  id: string;
  filename: string;
  status: 'processing' | 'ready' | 'error';
  page_count: number | null;
  project_id?: string | null;
  created_at: string;
}

interface ChatSession {
  id: string;
  title: string;
  is_pinned: boolean;
  selected_document_ids: string[];
  created_at: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: { source: string; page: number; document_id: string }[];
}

export default function Dashboard() {
  const { showToast, confirm, prompt: showPrompt } = useNotifications();

  // Navigation & UI State
  const [view, setView] = useState<'library' | 'chat'>('library');
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [showFileManager, setShowFileManager] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [attachToProjectId, setAttachToProjectId] = useState<string | null>(null);
  const [isMoveMenuOpen, setIsMoveMenuOpen] = useState(false);
  const [openChatMenuId, setOpenChatMenuId] = useState<string | null>(null);
  
  // Preview State
  const [previewDocId, setPreviewDocId] = useState<string | null>(null);
  const [previewPage, setPreviewPage] = useState<number>(1);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingPdf, setLoadingPdf] = useState(false);

  // Data State
  const [projects, setProjects] = useState<Project[]>([]);
  const [allDocs, setAllDocs] = useState<Document[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [modalSelectedDocs, setModalSelectedDocs] = useState<string[]>([]);
  const [attachSelectedDocs, setAttachSelectedDocs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadingToProject, setUploadingToProject] = useState<string | null>(null);

  // Chat State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // --- FETCHING ---
  const fetchData = async (silent = false) => {
    try {
      const [projRes, docsRes, sessionRes] = await Promise.all([
        api.get('/rag/projects'),
        api.get('/rag/documents'),
        api.get('/rag/chats')
      ]);
      setProjects(projRes.data);
      setAllDocs(docsRes.data);
      setSessions(sessionRes.data);
    } catch (err) { 
      console.error('Dashboard data fetch failed');
    } finally { 
      if (!silent) setLoading(false); 
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Smarter polling: only poll when there are files in 'processing' status
  useEffect(() => {
    const hasProcessing = allDocs.some(d => d.status === 'processing');
    const intervalTime = hasProcessing ? 5000 : 30000; // Poll every 5s if processing, otherwise every 30s
    
    const interval = setInterval(() => fetchData(true), intervalTime);
    return () => clearInterval(interval);
  }, [allDocs]);

  useEffect(() => {
    if (activeSessionId) fetchMessages(activeSessionId);
  }, [activeSessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);

  useEffect(() => {
    const handleClickOutside = () => setOpenChatMenuId(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const fetchMessages = async (sid: string) => {
    try {
      const res = await api.get(`/rag/chats/${sid}/messages`);
      setMessages(res.data);
    } catch (err) { console.error('Failed to fetch messages'); }
  };

  // --- ACTIONS ---
  const handleCreateProject = () => {
    showPrompt({
      title: "New Project",
      message: "Enter a name for your new knowledge base.",
      placeholder: "Project name...",
      onConfirm: async (name) => {
        try {
          await api.post('/rag/projects', { name });
          showToast("Project created successfully!");
          fetchData(true);
        } catch (err) {
          showToast("Failed to create project", "error");
        }
      }
    });
  };

  const handleCreateProjectWithDocs = () => {
    if (modalSelectedDocs.length === 0) return;
    showPrompt({
      title: "Project from Selection",
      message: `Create a new project with ${modalSelectedDocs.length} documents.`,
      placeholder: "Project name...",
      onConfirm: async (name) => {
        try {
          const projRes = await api.post('/rag/projects', { name });
          await api.post('/rag/documents/bulk-move', { document_ids: modalSelectedDocs, project_id: projRes.data.id });
          setModalSelectedDocs([]);
          showToast("Project created with documents!");
          fetchData(true);
        } catch (err) {
          showToast("Operation failed", "error");
        }
      }
    });
  };

  const handleEditProject = (id: string, currentName: string) => {
    showPrompt({
      title: "Rename Project",
      message: "Enter a new name for this project.",
      defaultValue: currentName,
      onConfirm: async (newName) => {
        try {
          await api.patch(`/rag/projects/${id}`, { name: newName });
          showToast("Project renamed");
          fetchData(true);
        } catch (err) {
          showToast("Rename failed", "error");
        }
      }
    });
  };

  const handleDeleteProject = (id: string) => {
    confirm({
      title: "Delete Project?",
      message: "The documents will remain in your global library.",
      confirmText: "Delete",
      onConfirm: async () => {
        try {
          await api.delete(`/rag/projects/${id}`);
          showToast("Project deleted");
          fetchData(true);
        } catch (err) {
          showToast("Delete failed", "error");
        }
      }
    });
  };

  const handleFileUpload = async (projectId: string | null, e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploadingToProject(projectId || 'global');
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) formData.append('files', files[i]);
    try {
      const url = projectId ? `/rag/upload?project_id=${projectId}` : '/rag/upload';
      await api.post(url, formData);
      showToast(`Uploading ${files.length} files...`, "info");
      fetchData(true);
    } catch (err) {
      showToast("Upload failed", "error");
    } finally {
      setUploadingToProject(null);
    }
  };

  const handleEditDoc = (id: string, currentName: string) => {
    showPrompt({
      title: "Rename File",
      message: "Enter a new filename.",
      defaultValue: currentName.replace('.pdf', ''),
      onConfirm: async (newName) => {
        try {
          await api.patch(`/rag/documents/${id}`, { filename: newName });
          showToast("File renamed");
          fetchData(true);
        } catch (err) {
          showToast("Rename failed", "error");
        }
      }
    });
  };

  const handleDeleteDoc = (id: string, permanent: boolean = false) => {
    const msg = permanent ? 'Permanently delete document from library?' : 'Remove document from this project?';
    confirm({
      title: permanent ? "Permanent Delete?" : "Remove from Project?",
      message: msg,
      confirmText: permanent ? "Delete Permanently" : "Remove",
      onConfirm: async () => {
        try {
          await api.delete(`/rag/documents/${id}${permanent ? '?permanent=true' : ''}`);
          showToast(permanent ? "File deleted permanently" : "File removed from project");
          fetchData(true);
        } catch (err) {
          showToast("Operation failed", "error");
        }
      }
    });
  };

  const handleBulkDelete = (docIds: string[], permanent: boolean = false) => {
    confirm({
      title: permanent ? "Delete Multiple Files?" : "Remove Multiple Files?",
      message: `Are you sure you want to process ${docIds.length} files?`,
      confirmText: "Continue",
      onConfirm: async () => {
        try {
          await api.post('/rag/documents/bulk-delete', { document_ids: docIds, permanent });
          if (permanent) setModalSelectedDocs([]); else setSelectedDocs([]);
          showToast("Bulk operation successful");
          fetchData(true);
        } catch (err) {
          showToast("Bulk operation failed", "error");
        }
      }
    });
  };

  const handleBulkMove = async (targetProjectId: string, docIds: string[]) => {
    try {
      await api.post('/rag/documents/bulk-move', { document_ids: docIds, project_id: targetProjectId });
      showToast(`Moved ${docIds.length} files`);
      fetchData(true);
    } catch (err) {
      showToast("Move failed", "error");
    }
  };

  const handleAttachDocs = async () => {
    if (!attachToProjectId || attachSelectedDocs.length === 0) return;
    await handleBulkMove(attachToProjectId, attachSelectedDocs);
    setAttachSelectedDocs([]); setShowAttachModal(false); setAttachToProjectId(null);
  };

  const handleRenameChat = (id: string, currentTitle: string) => {
    showPrompt({
      title: "Rename Chat",
      message: "Enter a new title for this conversation.",
      defaultValue: currentTitle,
      onConfirm: async (newTitle) => {
        try {
          await api.patch(`/rag/chats/${id}`, { title: newTitle });
          setOpenChatMenuId(null);
          showToast("Chat renamed");
          fetchData(true);
        } catch (err) {
          showToast("Rename failed", "error");
        }
      }
    });
  };

  const handleTogglePinChat = async (session: ChatSession) => {
    try {
      await api.patch(`/rag/chats/${session.id}`, { is_pinned: !session.is_pinned });
      setOpenChatMenuId(null);
      showToast(session.is_pinned ? "Chat unpinned" : "Chat pinned");
      fetchData(true);
    } catch (err) {
      showToast("Operation failed", "error");
    }
  };

  const handleDeleteChat = (id: string) => {
    confirm({
      title: "Delete Chat?",
      message: "This will permanently delete the conversation history.",
      confirmText: "Delete",
      onConfirm: async () => {
        try {
          await api.delete(`/rag/chats/${id}`);
          if (activeSessionId === id) {
            setView('library');
            setActiveSessionId(null);
          }
          setOpenChatMenuId(null);
          showToast("Chat deleted");
          fetchData(true);
        } catch (err) {
          showToast("Delete failed", "error");
        }
      }
    });
  };

  const toggleDocSelection = (docId: string, type: 'main' | 'modal' | 'attach' = 'main') => {
    const setter = type === 'main' ? setSelectedDocs : type === 'modal' ? setModalSelectedDocs : setAttachSelectedDocs;
    setter(p => p.includes(docId) ? p.filter(id => id !== docId) : [...p, docId]);
  };

  const handleSelectAllInProject = (docs: Document[]) => {
    const readyDocIds = docs.filter(d => d.status === 'ready').map(d => d.id);
    const allSelected = readyDocIds.length > 0 && readyDocIds.every(id => selectedDocs.includes(id));
    if (allSelected) setSelectedDocs(prev => prev.filter(id => !readyDocIds.includes(id)));
    else setSelectedDocs(prev => Array.from(new Set([...prev, ...readyDocIds])));
  };

  const handleSelectAllInModal = () => {
    const readyDocIds = allDocs.filter(d => d.status === 'ready').map(d => d.id);
    const allSelected = readyDocIds.length > 0 && readyDocIds.every(id => modalSelectedDocs.includes(id));
    if (allSelected) setModalSelectedDocs([]);
    else setModalSelectedDocs(readyDocIds);
  };

  const handleStartChat = async (selection: string[]) => {
    if (selection.length === 0) return;
    let projectId: string | null = null;
    for (const proj of projects) {
      if (selection.every(id => proj.documents.map(d => d.id).includes(id))) {
        projectId = proj.id;
        break;
      }
    }
    try {
      const res = await api.post('/rag/chats', { selected_document_ids: selection, project_id: projectId });
      setSessions([res.data, ...sessions]);
      setActiveSessionId(res.data.id);
      setView('chat');
      setShowFileManager(false);
      setSelectedDocs([]);
      setModalSelectedDocs([]);
      showToast("Chat session started!");
    } catch (err) {
      showToast("Could not start chat", "error");
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !activeSessionId || asking) return;

    const userQ = question;
    setQuestion('');
    setAsking(true);

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: userQ };
    setMessages(prev => [...prev, userMsg]);

    const aiMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: aiMsgId, role: 'assistant', content: '' }]);

    const performStream = async () => {
      const response = await fetch(`http://localhost:8000/api/v1/rag/chats/${activeSessionId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQ }),
        credentials: 'include' 
      });

      if (response.status === 401) {
        try {
          await api.post('/auth/refresh', {});
          return performStream(); 
        } catch (e) {
          window.location.href = '/login';
          return;
        }
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          accumulatedContent += decoder.decode(value, { stream: true });
          setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: accumulatedContent } : m));
        }
      }
      fetchMessages(activeSessionId);
    };

    try {
      await performStream();
    } catch (err) {
      showToast("AI response failed", "error");
      setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: 'Error getting response.' } : m));
    } finally {
      setAsking(false);
    }
  };

  const handleSourceClick = async (docId: string, page: number) => {
    setPreviewPage(page);
    if (docId === previewDocId && previewUrl) return;
    setLoadingPdf(true);
    setPreviewDocId(docId);
    try {
      const response = await api.get(`/rag/documents/${docId}/file`, { responseType: 'blob' });
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      setPreviewUrl(url);
    } catch (err) {
      showToast("Could not load PDF file", "error");
      setPreviewDocId(null);
    } finally {
      setLoadingPdf(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full text-white font-bold"><Loader2 className="animate-spin text-primary" size={40} /></div>;

  return (
    <div className="flex h-full w-full text-white text-left relative overflow-hidden bg-[#030712]">
      
      {/* SIDEBAR */}
      <aside className="w-72 flex-shrink-0 flex flex-col bg-[#0b0e14] border-r border-white/5 overflow-hidden transition-all duration-300">
        <div className="p-4 border-b border-white/5">
          <button 
            onClick={() => setView('library')} 
            className={`w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all hover:scale-[1.02] shadow-lg ${view === 'library' ? 'bg-white/10 text-white border-white/10 border' : 'bg-primary text-white shadow-primary/20'}`}
          >
            <Library size={18} /> Knowledge Hub
          </button>
        </div>
        
        <div className="flex-grow overflow-y-auto p-3 space-y-1 custom-scrollbar relative">
          <p className="px-4 py-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">History</p>
          {sessions.map(s => (
            <div key={s.id} className="relative group/session px-1 text-white">
              <button 
                onClick={() => { setActiveSessionId(s.id); setView('chat'); setPreviewDocId(null); setPreviewUrl(null); }} 
                className={`w-full p-3 pr-12 rounded-xl transition-all flex items-center gap-3 relative ${activeSessionId === s.id && view === 'chat' ? 'bg-white/10 text-white border-white/10 border' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
              >
                <MessageSquare size={16} className={`flex-shrink-0 ${activeSessionId === s.id && view === 'chat' ? 'text-primary' : ''}`} />
                <div className="min-w-0 flex-grow flex items-center gap-2">
                  <p className="truncate text-xs font-bold">{s.title}</p>
                  {s.is_pinned && <Pin size={12} className="text-primary fill-current flex-shrink-0" />}
                </div>
              </button>
              <button onClick={(e) => { e.stopPropagation(); setOpenChatMenuId(openChatMenuId === s.id ? null : s.id); }} className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-600 hover:text-white opacity-0 group-hover/session:opacity-100 transition-opacity z-10"><MoreVertical size={16} /></button>
              <AnimatePresence>
                {openChatMenuId === s.id && (
                  <motion.div 
                    onClick={(e) => e.stopPropagation()} 
                    initial={{ scale: 0.9, opacity: 0 }} 
                    animate={{ scale: 1, opacity: 1 }} 
                    exit={{ scale: 0.9, opacity: 0 }} 
                    className="absolute right-0 mt-8 w-48 bg-[#0b0e14] border border-white/10 rounded-2xl shadow-2xl p-2 z-[150] text-white"
                  >
                    <button onClick={() => handleTogglePinChat(s)} className="w-full p-3 hover:bg-white/5 text-left text-[10px] font-black uppercase tracking-widest flex items-center gap-2 rounded-xl transition-colors">{s.is_pinned ? <><PinOff size={14}/> Unpin</> : <><Pin size={14}/> Pin</>}</button>
                    <button onClick={() => handleRenameChat(s.id, s.title)} className="w-full p-3 hover:bg-white/5 text-left text-[10px] font-black uppercase tracking-widest flex items-center gap-2 rounded-xl transition-colors"><Edit2 size={14}/> Rename</button>
                    <button onClick={() => handleDeleteChat(s.id)} className="w-full p-3 hover:bg-red-500/10 text-red-500 text-left text-[10px] font-black uppercase tracking-widest flex items-center gap-2 rounded-xl transition-colors"><Trash2 size={14}/> Delete</button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-grow flex h-full relative overflow-hidden bg-[#030712]">
        <AnimatePresence mode="wait">
          {view === 'library' ? (
            <motion.div key="library" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col h-full w-full overflow-y-auto custom-scrollbar p-10 max-w-6xl mx-auto space-y-10">
              <header className="flex items-end justify-between text-white font-black">
                <div>
                  <h1 className="text-6xl font-black tracking-tightest text-white">Knowledge <span className="gradient-text">Base.</span></h1>
                  <p className="text-gray-400 text-lg font-medium mt-3 max-w-2xl leading-relaxed">
                    Centralize your documentation and unlock deep insights with your private AI assistant.
                  </p>
                </div>
                <div className="flex gap-3">
                  <AnimatePresence>{selectedDocs.length > 0 && (<motion.button initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.8, opacity: 0 }} whileHover={{ scale: 1.05 }} onClick={() => handleStartChat(selectedDocs)} className="px-8 py-3 bg-accent text-white rounded-2xl font-black text-sm shadow-xl shadow-accent/20 flex items-center gap-2 transition-all">Start Chat with {selectedDocs.length} Files</motion.button>)}</AnimatePresence>
                  <button onClick={() => setShowFileManager(true)} className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl text-gray-300 border border-white/5 transition-all shadow-lg"><Files size={24} /></button>
                  <button onClick={handleCreateProject} className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl text-gray-300 border border-white/5 transition-all shadow-lg"><FolderPlus size={24} /></button>
                </div>
              </header>

              <div className="grid grid-cols-1 gap-10 pb-20 text-white font-black">
                {projects.map(proj => {
                  const readyDocIds = proj.documents.filter(d => d.status === 'ready').map(d => d.id);
                  const isAllSelected = readyDocIds.length > 0 && readyDocIds.every(id => selectedDocs.includes(id));
                  return (
                    <section key={proj.id} className="space-y-4">
                      <div className="flex items-center justify-between px-2">
                        <div className="flex items-center gap-3"><Folder className="text-primary" size={24} /><h3 className="text-xl font-bold text-white">{proj.name}</h3><span className="text-xs font-bold text-gray-500 bg-white/5 px-2 py-1 rounded-md">{proj.documents.length} Files</span></div>
                        <div className="flex items-center gap-4">
                          <button onClick={() => handleSelectAllInProject(proj.documents)} className="text-[10px] font-black uppercase text-gray-500 hover:text-white transition-colors">{isAllSelected ? 'Deselect All' : 'Select All Ready'}</button>
                          <button onClick={() => { setAttachToProjectId(proj.id); setShowAttachModal(true); }} className="text-gray-500 hover:text-white transition-colors" title="Attach Existing"><LinkIcon size={18} /></button>
                          <button onClick={() => handleEditProject(proj.id, proj.name)} className="text-gray-500 hover:text-white transition-colors"><Edit2 size={18} /></button>
                          <label className="cursor-pointer text-gray-500 hover:text-white transition-colors"><Upload size={18} /><input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(proj.id, e)} /></label>
                          <button onClick={() => handleDeleteProject(proj.id)} className="text-gray-500 hover:text-red-500 transition-colors"><Trash2 size={18} /></button>
                        </div>
                      </div>
                      <div className="bg-white/[0.02] border border-white/5 rounded-[2.5rem] overflow-hidden shadow-2xl">
                        {proj.documents.map((doc) => {
                          const isSelected = selectedDocs.includes(doc.id);
                          return (
                            <div key={doc.id} className={`px-8 py-5 flex items-center justify-between transition-all border-b border-white/5 last:border-b-0 hover:bg-white/[0.03] ${isSelected ? 'bg-primary/5' : ''}`}>
                              <div className="flex items-center gap-4 flex-grow min-w-0"><FileText size={18} className="text-gray-600" /><p className="text-sm font-bold text-white truncate">{doc.filename}</p></div>
                              <div className="flex items-center gap-6">
                                <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full ${doc.status === 'ready' ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'}`}>{doc.status}</span>
                                <div className="flex items-center gap-2 border-l border-white/10 pl-6">
                                  <button onClick={() => handleEditDoc(doc.id, doc.filename)} className="p-2 text-gray-500 hover:text-white transition-colors"><Edit2 size={14} /></button>
                                  <button onClick={() => handleDeleteDoc(doc.id, false)} className="p-2 text-gray-500 hover:text-red-500 transition-colors"><X size={14} /></button>
                                  <button onClick={() => doc.status === 'ready' && toggleDocSelection(doc.id)} className="ml-4">{isSelected ? <CheckCircle size={22} className="text-primary shadow-[0_0_15px_rgba(99,102,241,0.5)]" /> : <Circle size={22} className="text-gray-800 hover:text-gray-600" />}</button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </section>
                  );
                })}
              </div>
            </motion.div>
          ) : (
            <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex w-full h-full relative">
              
              <div className={`flex-grow flex flex-col h-full transition-all duration-500 ${previewDocId ? 'w-1/2 border-r border-white/5' : 'w-full'}`}>
                <header className="flex-shrink-0 py-6 px-10 flex items-center justify-between border-b border-white/5 text-white">
                  <div className="flex items-center gap-4">
                    <button onClick={() => { setView('library'); setPreviewDocId(null); setPreviewUrl(null); }} className="p-2 hover:bg-white/5 rounded-full text-gray-400"><ArrowLeft size={20} /></button>
                    <h3 className="font-black text-xl text-white">{sessions.find(s => s.id === activeSessionId)?.title}</h3>
                  </div>
                  {previewDocId && <button onClick={() => { setPreviewDocId(null); setPreviewUrl(null); }} className="flex items-center gap-2 text-[10px] font-black uppercase text-gray-500 hover:text-white"><Minimize2 size={14}/> Close Preview</button>}
                </header>

                <div className="flex-grow overflow-y-auto custom-scrollbar pt-10 pb-40 px-10">
                  <div className={`max-w-4xl mx-auto space-y-12 ${previewDocId ? 'max-w-full' : ''}`}>
                    {messages.map((msg, i) => (
                      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[90%] ${msg.role === 'user' ? 'bg-white/5 p-6 rounded-[2rem] border border-white/5 shadow-xl' : ''}`}>
                          {msg.role === 'assistant' && (
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-black text-[10px] shadow-lg shadow-primary/30">AI</div>
                              <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Assistant</span>
                            </div>
                          )}
                          <div className="text-[16px] leading-[1.8] text-gray-200 prose prose-invert prose-sm max-w-none font-medium">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                          </div>
                          {msg.sources?.length ? (
                            <div className="mt-8 pt-4 border-t border-white/10 flex flex-wrap gap-2 text-white font-black">
                              {msg.sources.map((s, si) => <button key={si} onClick={() => handleSourceClick(s.document_id, s.page)} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-[10px] font-black text-gray-500 uppercase border border-white/5 transition-all flex items-center gap-2"><BookOpen size={12}/> {s.source} (p. {s.page})</button>)}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>
                </div>

                <div className="absolute bottom-10 left-0 right-0 px-6 z-20">
                  <div className="max-w-4xl mx-auto relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-accent/50 rounded-[2.5rem] opacity-0 blur-2xl group-focus-within:opacity-20 transition-all duration-700" />
                    <form onSubmit={handleAsk} className="relative bg-[#0b0e14]/80 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] p-3 flex items-center gap-3 shadow-2xl">
                      <button type="button" onClick={() => setView('library')} className="p-4 text-gray-500 hover:text-white hover:bg-white/5 rounded-full transition-all"><Plus size={24} /></button>
                      <input type="text" placeholder="Ask a question..." value={question} onChange={(e) => setQuestion(e.target.value)} disabled={asking} className="flex-grow bg-transparent px-2 py-4 text-white font-medium outline-none text-lg" />
                      <button type="submit" disabled={!question.trim() || asking} className="w-14 h-14 bg-primary text-white rounded-full flex items-center justify-center hover:scale-105 active:scale-90 transition-all shadow-xl shadow-primary/20 disabled:opacity-50"><Send size={24} /></button>
                    </form>
                  </div>
                </div>
              </div>

              <AnimatePresence>
                {previewDocId && (
                  <motion.div initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={{ type: 'spring', damping: 25, stiffness: 200 }} className="w-1/2 h-full bg-[#0b0e14] flex flex-col shadow-[-20px_0_50px_rgba(0,0,0,0.5)]">
                    <header className="p-4 border-b border-white/5 flex items-center justify-between bg-black/20 text-white">
                      <div className="flex items-center gap-3"><div className="p-2 bg-primary/20 text-primary rounded-lg"><FileText size={18} /></div><p className="text-sm font-bold text-white truncate max-w-[200px]">{allDocs.find(d => d.id === previewDocId)?.filename}</p></div>
                      <div className="flex items-center gap-4"><span className="text-[10px] font-black text-gray-500 uppercase tracking-widest bg-white/5 px-2 py-1 rounded">Page {previewPage}</span><button onClick={() => { setPreviewDocId(null); setPreviewUrl(null); }} className="p-2 hover:bg-white/10 rounded-lg transition-colors"><X size={20} /></button></div>
                    </header>
                    <div className="flex-grow bg-[#1a1d23] relative">
                      {loadingPdf && <div className="absolute inset-0 flex items-center justify-center bg-[#0b0e14]/50 z-30"><Loader2 className="animate-spin text-primary" size={32} /></div>}
                      {previewUrl && (
                        <iframe key={`${previewUrl}-${previewPage}`} src={`${previewUrl}#page=${previewPage}&toolbar=0&navpanes=0`} className="w-full h-full border-none" title="PDF Preview" />
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* GLOBAL MODALS */}
      <AnimatePresence>
        {showFileManager && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-xl text-white font-black">
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-5xl h-[85vh] bg-[#0b0e14] rounded-[3rem] border border-white/10 shadow-2xl flex flex-col overflow-hidden text-white font-black">
              <header className="p-8 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
                <div className="flex items-center gap-4"><div className="w-12 h-12 bg-primary text-white rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20"><Files size={24} /></div><div className="flex-grow font-black font-black uppercase"><h2 className="text-3xl font-black tracking-tighter text-white font-black uppercase">Library</h2><p className="text-sm text-gray-500 font-bold uppercase tracking-widest text-white">Document Management</p></div></div>
                <div className="flex items-center gap-4">
                  <button onClick={(e) => { e.stopPropagation(); handleSelectAllInModal(); }} className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest border border-white/10 transition-all flex items-center gap-2">
                    {allDocs.filter(d => d.status === 'ready').length > 0 && allDocs.filter(d => d.status === 'ready').every(id => modalSelectedDocs.includes(id.id)) && modalSelectedDocs.length > 0 ? <CheckSquare size={14}/> : <Square size={14}/>}
                    Select All
                  </button>
                  {modalSelectedDocs.length > 0 && (
                    <div className="flex gap-3">
                      <button onClick={(e) => { e.stopPropagation(); handleBulkDelete(modalSelectedDocs, true); }} className="px-6 py-2.5 bg-red-500 text-white rounded-xl font-bold text-xs flex items-center gap-2 shadow-lg shadow-red-500/20"><Trash2 size={14} /> Delete</button>
                      <button onClick={(e) => { e.stopPropagation(); handleCreateProjectWithDocs(); }} className="px-6 py-2.5 bg-accent text-white rounded-xl font-bold text-xs flex items-center gap-2 shadow-lg shadow-accent/20">New Project</button>
                      <div className="relative">
                        <button onClick={(e) => { e.stopPropagation(); setIsMoveMenuOpen(!isMoveMenuOpen); }} className="px-6 py-2.5 bg-primary text-white rounded-xl font-bold text-xs flex items-center gap-2 shadow-lg shadow-primary/20">Move to... <ChevronDown size={14} /></button>
                        <AnimatePresence>{isMoveMenuOpen && (<motion.div onClick={(e) => e.stopPropagation()} initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 10, opacity: 0 }} className="absolute right-0 mt-2 w-64 bg-[#0b0e14] border border-white/10 rounded-2xl shadow-2xl p-2 z-[110] text-white font-black"><p className="px-4 py-2 text-[10px] font-bold text-gray-500 uppercase border-b border-white/5 mb-2 font-bold">Target Project</p>{projects.map(p => (<button key={p.id} onClick={() => { handleBulkMove(p.id, modalSelectedDocs); setModalSelectedDocs([]); setIsMoveMenuOpen(false); }} className="w-full p-3 hover:bg-primary/10 text-left text-xs font-bold rounded-xl flex items-center justify-between group transition-colors text-white font-bold">{p.name}<ArrowRight size={12} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all text-white font-bold" /></button>))}</motion.div>)}</AnimatePresence>
                      </div>
                    </div>
                  )}
                  <button onClick={() => setShowFileManager(false)} className="p-3 hover:bg-white/5 rounded-2xl text-gray-500 transition-all"><X size={24} /></button>
                </div>
              </header>
              <div className="flex-grow overflow-y-auto custom-scrollbar text-white font-black">
                {allDocs.map(doc => {
                  const isSelected = modalSelectedDocs.includes(doc.id);
                  const proj = projects.find(p => p.id === doc.project_id);
                  return (
                    <div key={doc.id} className={`px-10 py-5 flex items-center justify-between border-b border-white/5 hover:bg-white/[0.02] transition-all ${isSelected ? 'bg-primary/5' : ''}`}>
                      <div className="flex items-center gap-6"><div onClick={(e) => { e.stopPropagation(); doc.status === 'ready' && toggleDocSelection(doc.id, 'modal'); }} className="cursor-pointer text-white font-black">{isSelected ? <CheckCircle size={24} className="text-primary shadow-[0_0_15px_rgba(99,102,241,0.5)]" /> : <Circle size={24} className="text-gray-800" />}</div><div className="flex items-center gap-4 text-white font-black"><FileText size={20} className="text-gray-600 font-black" /><p className="text-sm font-bold text-white truncate max-w-xs">{doc.filename}</p><span className="px-2 py-0.5 bg-white/5 text-gray-500 rounded text-[9px] font-black uppercase">{proj?.name || 'Unassigned'}</span></div></div>
                      <div className="flex items-center gap-4 text-white font-black">
                        <button onClick={(e) => { e.stopPropagation(); handleEditDoc(doc.id, doc.filename); }} className="p-2 text-gray-600 hover:text-white transition-all"><Edit2 size={16} /></button>
                        <button onClick={(e) => { e.stopPropagation(); handleDeleteDoc(doc.id, true); }} className="p-2 text-gray-600 hover:text-red-500 transition-all"><Trash2 size={18} /></button>
                      </div>
                    </div>
                  );
                })}
              </div>
              <footer className="p-8 bg-white/[0.02] border-t border-white/10 flex justify-center gap-4 text-white font-black font-black uppercase font-black">
                {modalSelectedDocs.length > 0 && (<button onClick={() => handleStartChat(modalSelectedDocs)} className="px-10 py-4 bg-accent text-white rounded-2xl font-black text-sm shadow-xl shadow-accent/30 hover:scale-105 transition-all text-white font-black">Start Chat with Selected</button>)}
                <label className="px-10 py-4 bg-white/5 hover:bg-white/10 text-white rounded-2xl font-black text-sm border border-white/10 transition-all cursor-pointer flex items-center gap-2 font-black font-black uppercase"><Upload size={18}/> Upload New Files<input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(null, e)} /></label>
              </footer>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showAttachModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm text-white text-left font-black">
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="w-full max-w-2xl glass-effect rounded-[3rem] border border-white/10 shadow-2xl flex flex-col overflow-hidden text-white font-black">
              <header className="p-8 border-b border-white/10 flex items-center justify-between bg-white/5 text-white">
                <div><h2 className="text-2xl font-black tracking-tighter text-white font-black uppercase">Attach Files</h2><p className="text-sm text-gray-500 font-medium text-white">Add documents to <span className="text-primary font-black uppercase">{projects.find(p => p.id === attachToProjectId)?.name}</span></p></div>
                <button onClick={() => { setShowAttachModal(false); setAttachSelectedDocs([]); }} className="p-2 text-gray-500 hover:text-white transition-colors bg-white/5 rounded-xl"><X size={24} /></button>
              </header>
              <div className="flex-grow overflow-y-auto p-8 space-y-3 custom-scrollbar text-white font-black">
                {allDocs.filter(d => d.project_id !== attachToProjectId).map(doc => {
                  const isSelected = attachSelectedDocs.includes(doc.id);
                  return (
                    <div key={doc.id} onClick={() => doc.status === 'ready' && toggleDocSelection(doc.id, 'attach')} className={`p-4 rounded-2xl border flex items-center justify-between cursor-pointer transition-all ${isSelected ? 'bg-primary/10 border-primary' : 'bg-white/5 border-white/5 hover:border-white/10'}`}>
                      <div className="flex items-center gap-3 min-w-0 text-white font-black uppercase tracking-widest"><FileText className={doc.status === 'ready' ? 'text-green-400' : 'text-yellow-400'} size={18} /><p className="text-sm font-bold truncate text-white">{doc.filename}</p></div>
                      {isSelected ? <CheckCircle size={20} className="text-primary" /> : <Circle size={20} className="text-gray-600" />}
                    </div>
                  );
                })}
              </div>
              <footer className="p-6 bg-white/5 border-t border-white/10 flex justify-end gap-4 text-white font-black uppercase tracking-widest">
                <button onClick={() => { setShowAttachModal(false); setAttachSelectedDocs([]); }} className="px-6 py-3 text-sm font-bold text-gray-400 hover:text-white text-white font-black">Cancel</button>
                <button onClick={handleAttachDocs} disabled={attachSelectedDocs.length === 0} className="px-8 py-3 bg-primary text-white rounded-2xl font-black text-sm shadow-xl shadow-primary/20 disabled:opacity-50 font-black uppercase tracking-widest">Attach Selected</button>
              </footer>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
