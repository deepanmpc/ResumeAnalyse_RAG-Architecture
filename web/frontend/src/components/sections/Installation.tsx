import { useEffect } from "react";
import Prism from "prismjs";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const CodeBlock = ({ code, language }: { code: string; language: string }) => {
  useEffect(() => {
    Prism.highlightAll();
  }, []);

  return (
    <pre>
      <code className={`language-${language}`}>{code}</code>
    </pre>
  );
};

export function Installation() {
  const cloneRepoCode = `git clone https://github.com/deepanmpc/ResumeAnalyse_RAG-Architecture.git`;
  const installDepsCode = `cd ResumeAnalyse_RAG-Architecture\nnpm install`;
  const runBackendCode = `python main.py`;
  const runFrontendCode = `cd frontend\nnpm run dev`;

  return (
    <section id="installation" className="py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-center mb-12">
            Get Started Locally
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card className="bg-background/50">
              <CardHeader>
                <CardTitle>1. Clone Repository</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock code={cloneRepoCode} language="bash" />
              </CardContent>
            </Card>
            <Card className="bg-background/50">
              <CardHeader>
                <CardTitle>2. Install Dependencies</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock code={installDepsCode} language="bash" />
              </CardContent>
            </Card>
            <Card className="bg-background/50">
              <CardHeader>
                <CardTitle>3. Run Backend</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock code={runBackendCode} language="bash" />
              </CardContent>
            </Card>
            <Card className="bg-background/50">
              <CardHeader>
                <CardTitle>4. Run Frontend</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock code={runFrontendCode} language="bash" />
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
