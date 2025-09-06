import { Github } from "lucide-react";
import { Link } from "react-router-dom";

export function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-lg font-bold">ResumeAnalyse RAG</span>
          </Link>
          <a
            href="https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
          >
            <Github className="h-4 w-4" />
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
