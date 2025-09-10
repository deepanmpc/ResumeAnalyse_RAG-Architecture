import { motion } from 'framer-motion';
import { Github, Heart, Zap, Code, Database, Brain } from 'lucide-react';

const Footer = () => {
  const techStack = [
    { name: "React", icon: Code },
    { name: "TailwindCSS", icon: Zap },
    { name: "ChromaDB", icon: Database },
    { name: "LangChain", icon: Brain }
  ];

  return (
    <footer className="relative py-16 px-6 border-t border-border/20 overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-t from-muted/10 to-background" />
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <h3 className="text-2xl font-bold mb-4">
            <span className="text-gradient-primary">ResumeAnalyse</span>{' '}
            <span className="text-gradient-accent">RAG Architecture</span>
          </h3>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Advanced AI-powered resume matching with RAG architecture. 
            Streamlining recruitment with intelligent vector search and LLM summarization.
          </p>
        </motion.div>

        {/* Tech Stack */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="flex flex-wrap justify-center gap-6 mb-12"
        >
          {techStack.map((tech, index) => {
            const IconComponent = tech.icon;
            return (
              <div
                key={index}
                className="flex items-center gap-2 px-4 py-2 glass-card border border-border/30 rounded-full"
              >
                <IconComponent className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium">{tech.name}</span>
              </div>
            );
          })}
        </motion.div>

        {/* Links and Credits */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col md:flex-row justify-between items-center gap-6"
        >
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors group"
            >
              <Github className="w-5 h-5 group-hover:animate-pulse" />
              <span>View on GitHub</span>
            </a>

            <div className="flex items-center gap-2 text-muted-foreground">
              <span>Built with</span>
              <Heart className="w-4 h-4 text-red-400 animate-pulse" />
              <span>and AI</span>
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            © 2024 ResumeAnalyse RAG Architecture. Powered by modern AI.
          </div>
        </motion.div>

        {/* Decorative Elements */}
        <div className="absolute top-4 left-4 w-2 h-2 bg-primary rounded-full animate-ping" />
        <div className="absolute top-8 right-8 w-2 h-2 bg-secondary rounded-full animate-ping delay-1000" />
        <div className="absolute bottom-4 left-1/3 w-2 h-2 bg-accent rounded-full animate-ping delay-2000" />
      </div>
    </footer>
  );
};

export default Footer;