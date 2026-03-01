import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Shield, CreditCard, Calendar, Zap, LogOut, RefreshCcw, Loader2 as LucideLoader } from 'lucide-react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

interface UserData {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

interface SubscriptionData {
  subscription: {
    name: string;
    job_limit: number;
    max_concurrent_jobs: number;
  };
  status: string;
  started_at: string;
}

// Renamed to avoid conflict with lucide-react Loader2
const CustomLoader = ({ className, size }: { className?: string, size?: number }) => (
  <motion.div
    animate={{ rotate: 360 }}
    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
    className={className}
  >
    <RefreshCcw size={size} />
  </motion.div>
);

export default function Profile() {
  const [user, setUser] = useState<UserData | null>(null);
  const [sub, setSub] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userRes, subRes] = await Promise.all([
          api.get('/users/me'),
          api.get('/subscriptions/me')
        ]);
        setUser(userRes.data);
        setSub(subRes.data);
      } catch (err) {
        console.error('Failed to fetch profile data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <CustomLoader className="text-primary" size={40} />
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-20">
      <header className="space-y-2 text-center md:text-left">
        <h1 className="text-4xl font-black tracking-tighter">Account <span className="gradient-text">Settings.</span></h1>
        <p className="text-gray-400 font-medium text-lg">Manage your personal information and subscription plan.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-8">
          <section className="p-8 glass-effect rounded-[2.5rem] border border-white/5 space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <User size={20} className="text-primary" />
              Personal Information
            </h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Email Address</p>
                <div className="flex items-center gap-2 text-white font-medium bg-white/5 p-3 rounded-xl border border-white/5">
                  <Mail size={16} className="text-gray-500" />
                  {user?.email}
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Account Role</p>
                <div className="flex items-center gap-2 text-white font-medium bg-white/5 p-3 rounded-xl border border-white/5">
                  <Shield size={16} className="text-gray-500" />
                  {user?.role?.toUpperCase() || 'USER'}
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Member Since</p>
                <div className="flex items-center gap-2 text-white font-medium bg-white/5 p-3 rounded-xl border border-white/5">
                  <Calendar size={16} className="text-gray-500" />
                  {user ? new Date(user.created_at).toLocaleDateString() : '-'}
                </div>
              </div>
            </div>

            <button 
              onClick={handleLogout}
              className="mt-4 flex items-center gap-2 text-red-400 hover:text-red-300 font-bold transition-colors text-sm px-4 py-2 hover:bg-red-400/10 rounded-xl"
            >
              <LogOut size={18} />
              Sign Out from all devices
            </button>
          </section>
        </div>

        <aside className="space-y-8">
          <section className="p-8 bg-primary/10 border-2 border-primary/20 rounded-[2.5rem] relative overflow-hidden group">
            <Zap className="absolute -right-4 -top-4 text-primary/10 group-hover:scale-125 transition-transform duration-500" size={150} />
            
            <div className="relative z-10 space-y-6">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-primary uppercase tracking-widest">Active Plan</p>
                <h3 className="text-3xl font-black text-white">{sub?.subscription?.name || 'No'} Plan</h3>
              </div>

              <div className="space-y-4 pt-4 border-t border-primary/20">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 font-medium">Daily Limit</span>
                  <span className="text-white font-black">{sub?.subscription?.job_limit || 0} Jobs</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 font-medium">Concurrency</span>
                  <span className="text-white font-black">{sub?.subscription?.max_concurrent_jobs || 0} Tasks</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 font-medium">Status</span>
                  <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full text-[10px] font-black uppercase tracking-tighter">
                    {sub?.status || 'Inactive'}
                  </span>
                </div>
              </div>

              <button className="w-full py-3 bg-primary text-white rounded-xl font-black hover:scale-105 transition-all shadow-lg shadow-primary/20 text-sm">
                Upgrade Plan
              </button>
            </div>
          </section>

          <section className="p-8 glass-effect rounded-[2.5rem] border border-white/5 space-y-4">
            <h4 className="text-sm font-bold flex items-center gap-2">
              <CreditCard size={18} className="text-gray-400" />
              Billing Method
            </h4>
            <p className="text-xs text-gray-500 font-medium italic">No credit card attached to this account yet.</p>
          </section>
        </aside>
      </div>
    </div>
  );
}
