import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Star, Zap, Shield, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  {
    icon: <Zap className="text-primary" />,
    title: "Lightning Fast Jobs",
    desc: "Process complex background tasks with our optimized Redis worker queue."
  },
  {
    icon: <Shield className="text-accent" />,
    title: "Enterprise Security",
    desc: "JWT-based auth and subscription-level rate limiting protect your data."
  },
  {
    icon: <Globe className="text-green-400" />,
    title: "Global Scalability",
    desc: "Deploy anywhere and scale your SaaS horizontally without limits."
  }
];

export default function Home() {
  return (
    <div className="space-y-32 pb-24">
      {/* Hero Section */}
      <section className="relative pt-20 flex flex-col items-center text-center space-y-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="px-4 py-1 glass-effect rounded-full text-xs font-bold text-primary tracking-widest uppercase flex items-center gap-2"
        >
          <Star size={12} className="fill-current" />
          The future of background processing
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-6xl md:text-8xl font-black tracking-tighter leading-tight"
        >
          Scale Your Backend <br />
          <span className="gradient-text">Without Limits.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="max-w-2xl text-gray-400 text-lg md:text-xl font-medium"
        >
          A high-performance SaaS framework with integrated workers, subscriptions, and security. 
          Focus on your business, we handle the infrastructure.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <Link to="/register" className="px-8 py-4 bg-primary text-white rounded-2xl font-bold flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-2xl shadow-primary/30 group">
            Start Building Now
            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link to="/pricing" className="px-8 py-4 glass-effect hover:bg-white/10 text-white rounded-2xl font-bold transition-all">
            View Pricing
          </Link>
        </motion.div>

        {/* Animated Grid Background Placeholder */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -z-10 w-full h-[800px] bg-gradient-to-b from-primary/10 to-transparent blur-[120px] rounded-full pointer-events-none" />
      </section>

      {/* Features Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            className="p-8 glass-effect rounded-3xl group hover:border-primary/50 transition-all cursor-default"
          >
            <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-inner">
              {f.icon}
            </div>
            <h3 className="text-xl font-bold text-white mb-3 group-hover:text-primary transition-colors">{f.title}</h3>
            <p className="text-gray-400 font-medium leading-relaxed">
              {f.desc}
            </p>
          </motion.div>
        ))}
      </section>
    </div>
  );
}
