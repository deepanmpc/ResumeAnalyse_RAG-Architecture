import { useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float, Stars } from '@react-three/drei';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ArrowDown, Github, Zap } from 'lucide-react';
import * as THREE from 'three';

// 3D Animated Sphere Component
function AnimatedSphere() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime) * 0.2;
      meshRef.current.rotation.y += 0.01;
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    }
  });

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
      <Sphere ref={meshRef} args={[1, 64, 32]} scale={2}>
        <MeshDistortMaterial
          color="#4FC3F7"
          attach="material"
          distort={0.3}
          speed={2}
          roughness={0.1}
          metalness={0.8}
          emissive="#1565C0"
          emissiveIntensity={0.3}
        />
      </Sphere>
    </Float>
  );
}

// Floating Particles
function FloatingNodes() {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.002;
    }
  });

  const nodes = Array.from({ length: 8 }, (_, i) => {
    const angle = (i / 8) * Math.PI * 2;
    const radius = 4;
    return {
      position: [
        Math.cos(angle) * radius,
        Math.sin(angle * 0.5) * 2,
        Math.sin(angle) * radius,
      ] as [number, number, number],
      color: i % 2 === 0 ? "#7C4DFF" : "#00BCD4",
    };
  });

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => (
        <Float key={i} speed={1.5 + i * 0.1} rotationIntensity={0.2} floatIntensity={0.5}>
          <mesh position={node.position}>
            <sphereGeometry args={[0.1, 16, 16]} />
            <meshStandardMaterial
              color={node.color}
              emissive={node.color}
              emissiveIntensity={0.5}
              transparent
              opacity={0.8}
            />
          </mesh>
        </Float>
      ))}
    </group>
  );
}

const HeroSection = () => {
  const scrollToDashboard = () => {
    const dashboardSection = document.getElementById('dashboard');
    dashboardSection?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background">
      {/* 3D Canvas Background */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
          <ambientLight intensity={0.2} />
          <pointLight position={[10, 10, 10]} intensity={1} color="#4FC3F7" />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#7C4DFF" />
          <Stars radius={300} depth={60} count={1000} factor={7} saturation={0} fade />
          <AnimatedSphere />
          <FloatingNodes />
        </Canvas>
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/50 via-background/30 to-background z-10" />

      {/* Hero Content */}
      <div className="relative z-20 text-center px-6 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-6">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-muted-foreground">
              Powered by RAG + LLM Architecture
            </span>
          </div>

          <h1 className="text-6xl md:text-8xl font-bold mb-6 leading-tight">
            <span className="hero-text animate-glow">Smarter Resume</span>
            <br />
            <span className="hero-text">Analysis</span>
          </h1>

          <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Advanced AI-powered resume matching with RAG architecture. 
            Analyze, compare, and find the perfect candidates with intelligent vector search.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
        >
          <Button 
            onClick={scrollToDashboard}
            size="lg" 
            className="glass-button neon-glow px-8 py-4 text-lg font-semibold"
          >
            <Zap className="mr-2 w-5 h-5" />
            Start Analysis
          </Button>

          <Button 
            variant="outline" 
            size="lg"
            className="glass-card border-primary/30 hover:border-primary/50 px-8 py-4 text-lg"
            asChild
          >
            <a 
              href="https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <Github className="mr-2 w-5 h-5" />
              View on GitHub
            </a>
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto"
        >
          {[
            { title: "RAG Architecture", desc: "Vector search with ChromaDB" },
            { title: "LLM Integration", desc: "Powered by Ollama/Mistral" },
            { title: "Smart Matching", desc: "AI-driven resume analysis" }
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.8 + i * 0.1 }}
              className="glass-card p-6 text-center"
            >
              <h3 className="text-lg font-semibold text-gradient-primary mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground text-sm">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.2 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20"
      >
        <div className="animate-bounce">
          <ArrowDown className="w-6 h-6 text-muted-foreground" />
        </div>
      </motion.div>
    </section>
  );
};

export default HeroSection;