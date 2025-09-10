import { useEffect } from 'react';
import HeroSection from '@/components/HeroSection';
import InstallationSection from '@/components/InstallationSection';
import ResumeMatchingDashboard from '@/components/ResumeMatchingDashboard';
import ChatbotSection from '@/components/ChatbotSection';
import Footer from '@/components/Footer';
import FloatingChatBot from '@/components/FloatingChatBot';

const Index = () => {
  useEffect(() => {
    window.scrollTo(0, 0); // Scroll to the top on component mount
    // Smooth scroll behavior for anchor links
    const handleScroll = () => {
      const reveals = document.querySelectorAll('.scroll-reveal');
      reveals.forEach((element) => {
        const windowHeight = window.innerHeight;
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;

        if (elementTop < windowHeight - elementVisible) {
          element.classList.add('revealed');
        }
      });
    };

    window.addEventListener('scroll', handleScroll);
    // handleScroll(); // Check on initial load

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <HeroSection />
      <InstallationSection />
      <ResumeMatchingDashboard />
      <ChatbotSection />
      <Footer />
      <FloatingChatBot />
    </div>
  );
};

export default Index;
