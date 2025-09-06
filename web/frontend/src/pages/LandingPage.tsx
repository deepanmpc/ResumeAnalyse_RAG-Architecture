import { motion } from "framer-motion";
import { HeroAnimation } from "@/components/3d/HeroAnimation";
import { ChatbotSection } from "@/components/sections/ChatbotSection";

export function LandingPage() {
  return (
    <div className="relative">
      <section className="h-screen w-full flex flex-col items-center justify-center text-center relative">
        <div className="absolute top-0 left-0 w-full h-full">
          <HeroAnimation />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10"
        >
          <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-400">
            Smarter Resume Analysis with RAG + LLM
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            A futuristic approach to resume screening.
          </p>
        </motion.div>
      </section>
      <ChatbotSection />
    </div>
  );
}
