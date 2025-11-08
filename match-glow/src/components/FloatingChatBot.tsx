import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Zap, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';

const FloatingChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  const scrollToDashboard = () => {
    const dashboardSection = document.getElementById('dashboard');
    dashboardSection?.scrollIntoView({ behavior: 'smooth' });
    setIsOpen(false);
  };

  const scrollToChat = () => {
    const chatSection = document.getElementById('chatbot');
    chatSection?.scrollIntoView({ behavior: 'smooth' });
    setIsOpen(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-8 right-8 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0, opacity: 0, y: 20 }}
            transition={{ duration: 0.3, type: "spring" }}
            className="absolute bottom-20 right-0 flex flex-col gap-3 mb-2"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={scrollToDashboard}
                className="glass-button neon-glow px-6 py-3 rounded-full shadow-2xl relative overflow-hidden group min-w-[180px]"
              >
                <div className="absolute inset-0 bg-gradient-primary opacity-20 group-hover:opacity-30 transition-opacity" />
                <Upload className="w-5 h-5 mr-2" />
                <span className="font-semibold">Start Analysis</span>
              </Button>
            </motion.div>

            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={scrollToChat}
                className="glass-card border-2 border-primary/30 hover:border-primary/50 px-6 py-3 rounded-full shadow-lg min-w-[180px] bg-background/80 backdrop-blur-sm"
              >
                <MessageCircle className="w-5 h-5 mr-2" />
                <span className="font-semibold">Ask AI</span>
              </Button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main floating button */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.5, delay: 1 }}
      >
        <Button
          onClick={() => {
            if (isOpen) {
              setIsOpen(false);
            } else {
              setIsOpen(true);
            }
          }}
          size="lg"
          className="w-16 h-16 rounded-full glass-button neon-glow shadow-2xl relative overflow-hidden group"
        >
          <div className="absolute inset-0 bg-gradient-primary opacity-30 group-hover:opacity-40 transition-opacity" />
          <motion.div
            animate={{ rotate: isOpen ? 45 : 0 }}
            transition={{ duration: 0.3 }}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Zap className="w-6 h-6" />}
          </motion.div>
          
          {/* Pulsing indicator when closed */}
          {!isOpen && (
            <div className="absolute -top-1 -right-1">
              <div className="w-4 h-4 bg-primary rounded-full animate-ping" />
              <div className="absolute top-0 right-0 w-4 h-4 bg-primary rounded-full" />
            </div>
          )}
        </Button>
      </motion.div>

      {/* Close permanently button */}
      {isOpen && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          onClick={() => setIsVisible(false)}
          className="absolute -top-3 -left-3 w-8 h-8 rounded-full glass-card border border-border/30 hover:border-destructive/50 flex items-center justify-center text-muted-foreground hover:text-destructive transition-colors"
        >
          <X className="w-4 h-4" />
        </motion.button>
      )}
    </div>
  );
};

export default FloatingChatBot;