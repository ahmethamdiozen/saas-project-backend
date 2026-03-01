import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Upload, 
  FileText, 
  MessageSquare, 
  Send, 
  CheckCircle2, 
  Loader2, 
  RefreshCcw,
  X,
  Search,
  BookOpen
} from 'lucide-react';
import api from '../services/api';

interface Document {
  id: string;
  filename: string;
  status: 'processing' | 'ready' | 'error';
  page_count: number | null;
  created_at: string;
}

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  sources?: { source: string; page: number }[];
}

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [asking, setAsking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/rag/documents');
      setDocuments(res.data);
    } catch (err) {
      console.error('Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000); // Poll documents status
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/rag/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchDocuments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || asking) return;

    const userMsg = { role: 'user' as const, content: question };
    setChatHistory(prev => [...prev, userMsg]);
    setQuestion('');
    setAsking(true);

    try {
      const res = await api.post('/rag/ask', { question });
      setChatHistory(prev => [...prev, { 
        role: 'ai', 
        content: res.data.answer,
        sources: res.data.sources
      }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Sorry, I failed to process that question.' }]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pb-10 min-h-[85vh]">
      
      {/* LEFT: Documents Management (4 columns) */}
      <div className="lg:col-span-4 space-y-6">
        <header className="space-y-2">
          <h1 className="text-3xl font-black tracking-tighter">My <span className="gradient-text">Library.</span></h1>
          <p className="text-gray-400 text-sm font-medium">Upload PDFs to train your personal AI.</p>
        </header>

        {/* Upload Area */}
        <div className="relative group">
          <input 
            type="file" 
            accept=".pdf" 
            onChange={handleFileUpload}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            disabled={uploading}
          />
          <div className={`p-8 border-2 border-dashed rounded-[2rem] transition-all flex flex-col items-center justify-center gap-4 ${
            uploading ? 'bg-primary/5 border-primary/30' : 'bg-white/5 border-white/10 group-hover:border-primary/50 group-hover:bg-primary/5'
          }`}>
            <div className="w-12 h-12 bg-primary/20 text-primary rounded-xl flex items-center justify-center">
              {uploading ? <Loader2 className="animate-spin" /> : <Upload size={24} />}
            </div>
            <div className="text-center">
              <p className="font-bold text-white text-sm">Click or Drag PDF</p>
              <p className="text-gray-500 text-xs mt-1">Maximum 10MB per file</p>
            </div>
          </div>
        </div>

        {/* Documents List */}
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {documents.length === 0 && !loading ? (
              <div className="text-center py-10 text-gray-500 font-medium text-sm italic">No documents yet.</div>
            ) : (
              documents.map((doc) => (
                <motion.div
                  key={doc.id}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-4 glass-effect rounded-2xl border border-white/5 hover:border-white/10 transition-all flex items-center gap-4 group"
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    doc.status === 'ready' ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'
                  }`}>
                    {doc.status === 'ready' ? <CheckCircle2 size={18} /> : <Loader2 size={18} className="animate-spin" />}
                  </div>
                  <div className="flex-grow min-w-0">
                    <h4 className="text-sm font-bold text-white truncate group-hover:text-primary transition-colors">{doc.filename}</h4>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-tighter">
                      <span>{doc.page_count ? `${doc.page_count} Pages` : 'Processing'}</span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* RIGHT: Chat Interface (8 columns) */}
      <div className="lg:col-span-8 flex flex-col glass-effect rounded-[2.5rem] border border-white/5 overflow-hidden shadow-2xl relative">
        
        {/* Chat Header */}
        <div className="p-6 border-b border-white/5 bg-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent/20 text-accent rounded-xl flex items-center justify-center">
              <MessageSquare size={20} />
            </div>
            <div>
              <h3 className="font-bold text-white">Document Assistant</h3>
              <p className="text-[10px] text-green-400 font-black uppercase tracking-widest flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                Context Aware Ready
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
             <button onClick={() => setChatHistory([])} className="p-2 text-gray-500 hover:text-white transition-colors" title="Clear Chat">
               <RefreshCcw size={18} />
             </button>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-grow overflow-y-auto p-6 space-y-6 custom-scrollbar min-h-[400px]">
          {chatHistory.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-30 grayscale hover:opacity-50 transition-opacity">
              <div className="w-20 h-20 bg-white/10 rounded-full flex items-center justify-center">
                <Search size={40} />
              </div>
              <div>
                <p className="text-xl font-bold">Ask anything about your PDFs</p>
                <p className="text-sm">Upload documents on the left to get started.</p>
              </div>
            </div>
          ) : (
            chatHistory.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[85%] p-5 rounded-3xl ${
                  msg.role === 'user' 
                    ? 'bg-primary text-white rounded-br-none shadow-xl shadow-primary/20' 
                    : 'bg-white/5 text-gray-200 border border-white/5 rounded-bl-none'
                }`}>
                  <p className="text-sm font-medium leading-relaxed">{msg.content}</p>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                      {msg.sources.map((s, si) => (
                        <div key={si} className="px-2 py-1 bg-white/5 rounded-md text-[10px] font-bold text-gray-400 flex items-center gap-1 border border-white/5 hover:border-primary/30 transition-colors">
                          <BookOpen size={10} />
                          {s.source} (p. {s.page})
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))
          )}
          {asking && (
            <div className="flex justify-start">
              <div className="bg-white/5 p-5 rounded-3xl rounded-bl-none border border-white/5 flex gap-2 items-center">
                <Loader2 size={16} className="animate-spin text-primary" />
                <span className="text-sm font-bold text-gray-500 uppercase tracking-widest">AI is thinking...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Chat Input */}
        <div className="p-6 bg-white/5 border-t border-white/5">
          <form onSubmit={handleAsk} className="relative group">
            <input
              type="text"
              placeholder={documents.some(d => d.status === 'ready') ? "Ask a question..." : "Waiting for ready documents..."}
              disabled={asking || !documents.some(d => d.status === 'ready')}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="w-full pl-6 pr-16 py-5 bg-[#030712] border border-white/10 rounded-2xl text-white font-medium outline-none focus:border-primary focus:ring-4 ring-primary/10 transition-all placeholder:text-gray-600 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={asking || !question.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-12 h-12 bg-primary text-white rounded-xl flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20 disabled:opacity-50 disabled:grayscale"
            >
              <Send size={20} />
            </button>
          </form>
          <p className="mt-3 text-[10px] text-center text-gray-600 font-bold uppercase tracking-tighter">
            AI can make mistakes. Always check the original source.
          </p>
        </div>
      </div>
    </div>
  );
}
