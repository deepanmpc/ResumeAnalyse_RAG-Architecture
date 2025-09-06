import { Github } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">
            Smarter Resume Analysis with RAG + LLM
          </p>
          <div className="flex items-center gap-4">
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
      </div>
    </footer>
  );
}
