import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Zap, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';

const FloatingChatBot = () => {
  const [isVisible, setIsVisible] = useState(true);

  const scrollToDashboard = () => {
    const dashboardSection = document.getElementById('dashboard');
    dashboardSection?.scrollIntoView({ behavior: 'smooth' });
    setIsVisible(false);
  };

  const scrollToChat = () => {
    const chatSection = document.getElementById('chatbot');
    chatSection?.scrollIntoView({ behavior: 'smooth' });
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ duration: 0.3, delay: 2 }}
          className="flex flex-col gap-3"
        >
          {/* Close button */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 3 }}
            className="self-end"
          >
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsVisible(false)}
              className="w-8 h-8 rounded-full glass-card border border-border/30 hover:border-primary/50"
            >
              <X className="w-4 h-4" />
            </Button>
          </motion.div>

          {/* Action buttons */}
          <div className="flex flex-col gap-3">
            {/* Analyze Button */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                onClick={scrollToDashboard}
                className="glass-button neon-glow px-6 py-3 rounded-full shadow-2xl relative overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-primary opacity-20 group-hover:opacity-30 transition-opacity" />
                <Upload className="w-5 h-5 mr-2" />
                <span className="font-semibold">Start Analysis</span>
              </Button>
            </motion.div>

            {/* Chat Button */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                onClick={scrollToChat}
                variant="outline"
                className="glass-card border-secondary/30 hover:border-secondary/50 px-6 py-3 rounded-full shadow-lg"
              >
                <MessageCircle className="w-5 h-5 mr-2" />
                <span className="font-semibold">Ask AI</span>
              </Button>
            </motion.div>
          </div>

          {/* Pulsing indicator */}
          <div className="absolute -top-1 -right-1">
            <div className="w-3 h-3 bg-primary rounded-full animate-ping" />
            <div className="absolute top-0 right-0 w-3 h-3 bg-primary rounded-full" />
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default FloatingChatBot;