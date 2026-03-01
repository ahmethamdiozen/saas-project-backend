import { Routes, Route, Link, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Zap, LayoutDashboard, User as UserIcon, LogOut } from 'lucide-react';

// Real Pages
import Home from './pages/Home';
import Pricing from './pages/Pricing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    
    // Check login status on route change
    const checkLogin = () => setIsLoggedIn(!!localStorage.getItem('access_token'));
    checkLogin();

    return () => window.removeEventListener('scroll', handleScroll);
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsLoggedIn(false);
    navigate('/login');
  };

  return (
    <motion.nav 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-6 py-4 ${
        scrolled ? 'glass-effect py-2 shadow-2xl' : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="p-2 bg-primary rounded-xl group-hover:rotate-12 transition-transform shadow-lg shadow-primary/20">
            <Zap className="text-white" size={20} fill="currentColor" />
          </div>
          <span className="text-xl font-black tracking-tighter text-white">SAASIFY</span>
        </Link>

        <div className="hidden md:flex items-center gap-10">
          {!isLoggedIn ? (
            <>
              <Link to="/" className="text-sm font-bold text-gray-400 hover:text-white transition-all nav-link-hover">Home</Link>
              <Link to="/pricing" className="text-sm font-bold text-gray-400 hover:text-white transition-all nav-link-hover">Pricing</Link>
            </>
          ) : (
            <>
              <Link to="/dashboard" className={`flex items-center gap-2 text-sm font-bold transition-all nav-link-hover ${location.pathname === '/dashboard' ? 'text-white' : 'text-gray-400'}`}>
                <LayoutDashboard size={16} /> Dashboard
              </Link>
              <Link to="/profile" className={`flex items-center gap-2 text-sm font-bold transition-all nav-link-hover ${location.pathname === '/profile' ? 'text-white' : 'text-gray-400'}`}>
                <UserIcon size={16} /> Profile
              </Link>
            </>
          )}
        </div>

        <div className="flex items-center gap-6">
          {!isLoggedIn ? (
            <>
              <Link to="/login" className="text-sm font-bold text-gray-400 hover:text-white transition-colors">Login</Link>
              <Link to="/register" className="px-6 py-2.5 bg-primary hover:bg-primary-dark text-white text-sm font-black rounded-xl transition-all hover:scale-105 active:scale-95 shadow-xl shadow-primary/30">
                Get Started
              </Link>
            </>
          ) : (
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-red-400 transition-colors"
            >
              <LogOut size={18} /> Sign Out
            </button>
          )}
        </div>
      </div>
    </motion.nav>
  );
};

export default function App() {
  const location = useLocation(); // Already inside a Router context now

  return (
    <div className="min-h-screen bg-[#030712] text-white selection:bg-primary/30">
      <Navbar />
      <main className="pt-24 px-6 max-w-7xl mx-auto">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
          </Routes>
        </AnimatePresence>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-white/5 py-12 mt-20 text-center text-gray-500 text-sm font-medium">
        &copy; 2026 Saasify Framework. Built with React 19 & Tailwind v4.
      </footer>
    </div>
  );
}
