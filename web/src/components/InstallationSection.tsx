import { useState } from 'react';
import { motion } from 'framer-motion';
import { Copy, Terminal, Download, Play, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

const InstallationSection = () => {
  const { toast } = useToast();
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const installationSteps = [
    {
      title: "Clone Repository",
      description: "Download the ResumeAnalyse RAG Architecture project",
      code: "git clone https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git\ncd ResumeAnalyse_RAG-Architecture",
      icon: Download
    },
    {
      title: "Install Dependencies",
      description: "Set up Python dependencies and virtual environment",
      code: "python -m venv venv\nsource venv/bin/activate  # On Windows: venv\\Scripts\\activate\npip install -r requirements.txt",
      icon: Terminal
    },
    {
      title: "Configure Environment",
      description: "Set up your environment variables and API keys",
      code: "cp .env.example .env\n# Edit .env with your configurations\n# Add your LLM API keys if needed",
      icon: CheckCircle
    },
    {
      title: "Run the Application",
      description: "Start the backend server and web interface",
      code: "# Start the backend\npython app.py\n\n# In another terminal, start the frontend\nnpm install\nnpm run dev",
      icon: Play
    }
  ];

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      toast({
        title: "Copied!",
        description: "Code copied to clipboard",
      });
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      toast({
        title: "Failed to copy",
        description: "Please copy the code manually",
        variant: "destructive",
      });
    }
  };

  return (
    <section id="installation" className="py-20 px-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/5 to-background" />
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-secondary/10 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-gradient-primary">Quick Setup</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Get your RAG-powered resume analysis system running in minutes with our streamlined installation process.
          </p>
        </motion.div>

        <div className="grid gap-8">
          {installationSteps.map((step, index) => {
            const IconComponent = step.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                viewport={{ once: true }}
              >
                <Card className="glass-card p-8 hover:shadow-glow-primary transition-all duration-300">
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center">
                        <IconComponent className="w-6 h-6 text-primary-foreground" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-4">
                        <span className="text-2xl font-bold text-gradient-accent">
                          {index + 1}
                        </span>
                        <h3 className="text-2xl font-semibold">{step.title}</h3>
                      </div>

                      <p className="text-muted-foreground mb-6">
                        {step.description}
                      </p>

                      <div className="relative">
                        <div className="bg-muted/20 backdrop-blur-sm rounded-xl p-4 font-mono text-sm border border-border/50">
                          <pre className="whitespace-pre-wrap text-foreground">
                            {step.code}
                          </pre>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(step.code, index)}
                          className="absolute top-2 right-2 glass-button"
                        >
                          {copiedIndex === index ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <Card className="glass-card p-8 max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold mb-4 text-gradient-primary">
              Need Help?
            </h3>
            <p className="text-muted-foreground mb-6">
              Check out the detailed documentation on GitHub for troubleshooting and advanced configuration options.
            </p>
            <Button 
              variant="outline" 
              className="glass-button border-primary/30 hover:border-primary/50"
              asChild
            >
              <a 
                href="https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                View Documentation
              </a>
            </Button>
          </Card>
        </motion.div>
      </div>
    </section>
  );
};

export default InstallationSection;