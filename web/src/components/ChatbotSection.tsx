import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, MessageCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

const ChatbotSection = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm your AI assistant for resume analysis. Ask me about candidate strengths, skills, or request detailed summaries.",
      isBot: true,
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const mockResponses = [
    "Alex Chen shows exceptional expertise in machine learning with 5+ years of experience in Python and React. His background includes developing AI-powered applications and implementing scalable ML pipelines.",
    "Sarah Johnson demonstrates strong data science capabilities with proficiency in TensorFlow, SQL, and data visualization. She has led multiple analytics projects and excels in statistical modeling.",
    "Based on the uploaded resumes, the top candidates for this ML Engineer position are Alex Chen (92% match), Sarah Johnson (88% match), and Michael Rodriguez (85% match). Would you like detailed insights on any specific candidate?",
    "The skill gap analysis shows that most candidates have strong technical foundations, but may benefit from additional experience in cloud deployment and MLOps practices.",
    "I can help you analyze candidate qualifications, compare skill sets, generate summaries, or provide insights on the best matches for your requirements."
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const simulateTyping = async (response: string) => {
    setIsTyping(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
    
    setIsTyping(false);
    
    const newMessage: Message = {
      id: messages.length + 1,
      text: response,
      isBot: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputText,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');

    // Simulate bot response
    const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
    await simulateTyping(randomResponse);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const suggestedQuestions = [
    "Summarize top candidates' strengths",
    "What are the top skills across all candidates?",
    "Compare the top 3 candidates",
    "Identify skill gaps in the candidate pool"
  ];

  return (
    <section id="chatbot" className="py-20 px-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-t from-background via-muted/5 to-background" />
      <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-secondary/10 rounded-full blur-3xl animate-pulse" />

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-gradient-primary">AI-Powered</span>
            <br />
            <span className="text-gradient-accent">Resume Assistant</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Chat with our intelligent assistant to get detailed insights about candidates, skill analyses, and personalized recommendations.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Suggested Questions */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="lg:col-span-1"
          >
            <Card className="glass-card p-6 h-fit">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Quick Questions
              </h3>
              <div className="space-y-3">
                {suggestedQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    onClick={() => setInputText(question)}
                    className="w-full text-left justify-start h-auto p-3 text-xs leading-relaxed glass-button border border-border/50 hover:border-primary/30 whitespace-normal break-words min-h-[2.5rem]"
                  >
                    <span className="block w-full">{question}</span>
                  </Button>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Chat Interface */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="lg:col-span-3"
          >
            <Card className="glass-card p-6 h-[600px] flex flex-col">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
                <div className="w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center">
                  <Bot className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold">Resume Analysis Assistant</h3>
                  <p className="text-sm text-muted-foreground">AI-powered insights at your fingertips</p>
                </div>
                <div className="ml-auto flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-muted-foreground">Online</span>
                </div>
              </div>

              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  <AnimatePresence>
                    {messages.map((message) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                        className={`flex gap-3 ${message.isBot ? 'justify-start' : 'justify-end'}`}
                      >
                        {message.isBot && (
                          <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0">
                            <Bot className="w-4 h-4 text-primary-foreground" />
                          </div>
                        )}
                        
                        <div className={`max-w-[70%] ${message.isBot ? '' : 'order-first'}`}>
                          <div className={`p-4 rounded-2xl ${
                            message.isBot 
                              ? 'glass-card border border-border/50' 
                              : 'bg-gradient-primary text-primary-foreground'
                          }`}>
                            <p className="text-sm leading-relaxed">{message.text}</p>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1 px-2">
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>

                        {!message.isBot && (
                          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                            <User className="w-4 h-4 text-muted-foreground" />
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>

                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-3 justify-start"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                        <Bot className="w-4 h-4 text-primary-foreground" />
                      </div>
                      <div className="glass-card border border-border/50 p-4 rounded-2xl">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100" />
                          <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200" />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
                <div ref={messagesEndRef} />
              </ScrollArea>

              <div className="flex gap-3 mt-4 pt-4 border-t border-border/50">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about candidate analysis, skills, or comparisons..."
                  className="flex-1 glass-card border-border/50 focus:border-primary/50"
                />
                <Button 
                  onClick={handleSendMessage} 
                  disabled={!inputText.trim() || isTyping}
                  className="glass-button neon-glow px-6"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default ChatbotSection;