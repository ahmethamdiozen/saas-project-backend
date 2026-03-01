import { motion } from 'framer-motion';
import { Check, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

const tiers = [
  {
    name: "Free",
    price: "$0",
    desc: "Perfect for hobby projects",
    features: ["10 Daily Jobs", "1 Concurrent Job", "Basic Support", "2 Requests/min"],
    highlight: false
  },
  {
    name: "Pro",
    price: "$29",
    desc: "For growing businesses",
    features: ["100 Daily Jobs", "10 Concurrent Jobs", "Priority Support", "60 Requests/min", "Custom Metadata"],
    highlight: true
  },
  {
    name: "Enterprise",
    price: "$199",
    desc: "Scale without limits",
    features: ["Unlimited Jobs", "Unlimited Concurrency", "24/7 Support", "1000 Requests/min", "Dedicated Worker"],
    highlight: false
  }
];

export default function Pricing() {
  return (
    <div className="py-20 text-center space-y-20">
      <section className="space-y-6">
        <h2 className="text-5xl font-black tracking-tighter">Simple, Transparent <br /> <span className="gradient-text">Pricing.</span></h2>
        <p className="text-gray-400 max-w-xl mx-auto text-lg">Choose the plan that fits your needs. Scale up or down as you grow.</p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
        {tiers.map((t, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className={`flex flex-col p-10 rounded-[2.5rem] transition-all relative ${
              t.highlight 
                ? 'bg-primary/10 border-2 border-primary shadow-2xl shadow-primary/20 scale-105' 
                : 'glass-effect border border-white/5 hover:border-white/20'
            }`}
          >
            {t.highlight && (
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">
                Most Popular
              </div>
            )}
            
            <div className="space-y-4 mb-8">
              <h3 className="text-xl font-bold text-white">{t.name}</h3>
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-5xl font-black text-white">{t.price}</span>
                <span className="text-gray-400 font-medium">/month</span>
              </div>
              <p className="text-gray-400 text-sm font-medium">{t.desc}</p>
            </div>

            <div className="space-y-4 mb-10 text-left flex-grow">
              {t.features.map((f, fi) => (
                <div key={fi} className="flex items-center gap-3 text-sm font-medium text-gray-300">
                  <div className={`p-1 rounded-full ${t.highlight ? 'bg-primary/20 text-primary' : 'bg-white/5 text-gray-500'}`}>
                    <Check size={14} strokeWidth={3} />
                  </div>
                  {f}
                </div>
              ))}
            </div>

            <Link 
              to="/register" 
              className={`w-full py-4 rounded-2xl font-black transition-all hover:scale-105 active:scale-95 ${
                t.highlight 
                  ? 'bg-primary text-white shadow-xl shadow-primary/30' 
                  : 'bg-white/5 text-white hover:bg-white/10'
              }`}
            >
              Select Plan
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
