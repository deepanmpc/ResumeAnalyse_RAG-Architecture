import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, Users, Sliders, Eye, Settings, Zap, Target, Download, BrainCircuit } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

const ResumeMatchingDashboard = ({ setError }) => {
  const [topN, setTopN] = useState("5");
  const [customTopN, setCustomTopN] = useState("");

  const handleChat = async (resumeId: string) => {
    console.log(`Chat button clicked for resume ID: ${resumeId}`);

    try {
      // 1. Retrieve the full resume text embeddings from the API
      const response = await fetch(`http://localhost:8000/api/resume-embedding/${resumeId}`);
      if (!response.ok) {
        throw new Error(`Failed to retrieve resume embedding: ${response.status}`);
      }
      const data = await response.json();
      const resumeEmbedding = data.embedding;

      // 2. Send the embeddings to SLM_manager/augemented_generation.py as a JSON file
      // TODO: Implement the logic to send the embeddings to SLM_manager/augemented_generation.py
      // This might involve creating a new API endpoint or using an existing one

      // 3. Display the summarized information in the AI chatbot section
      // TODO: Implement the logic to display the summarized information in the AI chatbot section

      console.log("Resume embedding:", resumeEmbedding);
    } catch (error: any) {
      console.error("Error handling chat:", error);
      setError(error.message || "An unknown error occurred while handling chat.");
    }
  };

  const [threshold, setThreshold] = useState([75]);
  const [previewMode, setPreviewMode] = useState(true);
  const [jobDescription, setJobDescription] = useState<File | null>(null);
  const [resumes, setResumes] = useState<File[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any[]>([]);
  const [aiSummary, setAiSummary] = useState<string | null>(null);

  const handleJobDescriptionUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setJobDescription(file);
      setAnalysisComplete(false);
      setAnalysisResults([]);
      setAiSummary(null);
      setError(null);
    }
  };

  const handleResumeUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setResumes(files);
    setAnalysisComplete(false);
    setAnalysisResults([]);
    setAiSummary(null);
    setError(null);
  };

  const handleAnalysis = async () => {
    if (!jobDescription || resumes.length === 0) return;

    setIsAnalyzing(true);
    setAnalysisComplete(false);
    setError(null);
    setAiSummary(null);

    const formData = new FormData();
    formData.append('job_description', jobDescription);
    resumes.forEach(resume => {
      formData.append('resumes', resume);
    });

    try {
      const response = await fetch('http://localhost:8000/api/match-resumes', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const formattedResults = Object.entries(data.matches).map(([fileName, matchData]: [string, any]) => ({
        id: fileName,
        name: matchData.filename.split('/').pop()?.replace(/\.[^/.]+$/, "") || "Unknown",
        score: Math.round(matchData.match_percentage),
        experience: matchData.experience,
        highlight: matchData.text,
        skills: matchData.skills,
      }));

      setAnalysisResults(formattedResults);
      setAiSummary(data.summary);
      setAnalysisComplete(true);

    } catch (e: any) {
      console.error("Analysis failed:", e);
      setError(e.message || "An unknown error occurred during analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const actualTopN = topN === "custom" ? parseInt(customTopN) || 5 : parseInt(topN);
  
  const filteredResults = analysisResults
    .filter(result => result.score >= threshold[0])
    .slice(0, actualTopN);

  const handleExportResults = () => {
    const dataStr = JSON.stringify({ matches: analysisResults, summary: aiSummary }, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `resume_matches_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const controlSections = [
    {
      title: "Job Description",
      icon: FileText,
      content: (
        <div className="space-y-4">
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleJobDescriptionUpload}
            className="hidden"
            id="job-upload"
          />
          <label 
            htmlFor="job-upload"
            className="border-2 border-dashed border-primary/30 rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer block"
          >
            <Upload className="w-8 h-8 text-primary mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              {jobDescription ? jobDescription.name : "Upload Job Description"}
            </p>
            {jobDescription && (
              <p className="text-xs text-primary mt-1">✓ 1 file uploaded</p>
            )}
          </label>
        </div>
      )
    },
    {
      title: "Resume Upload",
      icon: Users,
      content: (
        <div className="space-y-4">
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            multiple
            onChange={handleResumeUpload}
            className="hidden"
            id="resume-upload"
          />
          <label 
            htmlFor="resume-upload"
            className="border-2 border-dashed border-secondary/30 rounded-xl p-8 text-center hover:border-secondary/50 transition-colors cursor-pointer block"
          >
            <Upload className="w-8 h-8 text-secondary mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              {resumes.length > 0 ? `${resumes.length} resume(s) selected` : "Upload Resume PDFs (Multiple files)"}
            </p>
            {resumes.length > 0 && (
              <p className="text-xs text-secondary mt-1">✓ {resumes.length} files uploaded</p>
            )}
          </label>
        </div>
      )
    },
    {
      title: "Top N Matches",
      icon: Target,
      content: (
        <div className="space-y-4">
          <Select value={topN} onValueChange={setTopN}>
            <SelectTrigger className="glass-card border-accent/30">
              <SelectValue placeholder="Select number of matches" />
            </SelectTrigger>
            <SelectContent className="glass-card border-accent/30">
              <SelectItem value="3">Top 3</SelectItem>
              <SelectItem value="5">Top 5</SelectItem>
              <SelectItem value="10">Top 10</SelectItem>
              <SelectItem value="15">Top 15</SelectItem>
              <SelectItem value="20">Top 20</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>
          
          {topN === "custom" && (
            <div className="mt-3">
              <input
                type="number"
                value={customTopN}
                onChange={(e) => setCustomTopN(e.target.value)}
                placeholder="Enter custom number"
                min="1"
                max="100"
                className="w-full px-3 py-2 rounded-lg glass-card border border-accent/30 focus:border-accent/50 outline-none text-sm"
              />
            </div>
          )}
          
          <p className="text-xs text-muted-foreground">
            Showing top {actualTopN} candidates
          </p>
        </div>
      )
    },
    {
      title: "Similarity Threshold",
      icon: Sliders,
      content: (
        <div className="space-y-4">
          <div className="flex justify-between text-sm">
            <span>Minimum Match Score</span>
            <span className="text-primary font-semibold">{threshold[0]}%</span>
          </div>
          <Slider
            value={threshold}
            onValueChange={setThreshold}
            max={100}
            min={0}
            step={1}
            className="w-full"
          />
        </div>
      )
    },
  ];

  return (
    <section id="dashboard" className="py-20 px-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-background via-muted/5 to-background" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse" />

      <div className="relative z-10 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-gradient-primary">Resume Matching</span>
            <br />
            <span className="text-gradient-accent">Dashboard</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Upload a job description and resumes to find the perfect matches using our advanced RAG architecture.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {controlSections.map((section, index) => {
            const IconComponent = section.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <Card className="glass-card p-6 hover:shadow-glow-primary transition-all duration-300 h-full">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                      <IconComponent className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <h3 className="font-semibold text-lg">{section.title}</h3>
                  </div>
                  {section.content}
                </Card>
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
        >
          <Button 
            size="lg" 
            className="glass-button neon-glow px-8 py-4 relative overflow-hidden group"
            onClick={handleAnalysis}
            disabled={!jobDescription || resumes.length === 0 || isAnalyzing}
          >
            <div className="absolute inset-0 bg-gradient-primary opacity-20 group-hover:opacity-30 transition-opacity" />
            {isAnalyzing ? (
              <>
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2" />
                Analyzing...
              </>
            ) : (
              <>
                <Zap className="mr-2 w-5 h-5" />
                Analyze {resumes.length} Resume{resumes.length !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </motion.div>

        {analysisComplete && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            {aiSummary && (
              <Card className="glass-card p-6 hover:shadow-glow-accent transition-all duration-300">
                 <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-gradient-accent flex items-center justify-center">
                      <BrainCircuit className="w-5 h-5 text-accent-foreground" />
                    </div>
                    <h3 className="font-semibold text-lg text-accent">AI-Generated Summary</h3>
                  </div>
                <p className="text-muted-foreground whitespace-pre-wrap">{aiSummary}</p>
              </Card>
            )}

            {filteredResults.length > 0 ? (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
                  <h3 className="text-2xl font-bold">
                    <span className="text-gradient-accent">Top Matches</span>
                    <span className="text-sm text-muted-foreground font-normal ml-2">
                      (Showing {filteredResults.length} of {analysisResults.length} total matches)
                    </span>
                  </h3>
                  
                  <Button
                    onClick={handleExportResults}
                    variant="outline"
                    className="glass-card border-secondary/30 hover:border-secondary/50 px-6 py-2"
                  >
                    <Download className="mr-2 w-4 h-4" />
                    Export All Results ({analysisResults.length})
                  </Button>
                </div>

                <div className="grid gap-6">
                  {filteredResults.map((candidate, index) => (
                    <motion.div
                      key={candidate.id}
                      initial={{ opacity: 0, x: -50 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.6, delay: index * 0.1 }}
                    >
                      <Card className="glass-card p-6 hover:shadow-glow-secondary transition-all duration-300 border-l-4 border-l-primary relative">
                        <div className="absolute top-4 right-4 bg-primary/20 text-primary px-2 py-1 rounded-full text-xs font-semibold">
                          #{index + 1}
                        </div>
                        
                        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-4 mb-3">
                              <h4 className="text-xl font-semibold">{candidate.name}</h4>
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                <span className="text-sm text-muted-foreground">{candidate.experience}</span>
                              </div>
                            </div>
                            
                            <p className="text-muted-foreground mb-4 whitespace-pre-wrap">{candidate.highlight}</p>

                            <div className="flex flex-wrap gap-2">
                              {candidate.skills.map((skill: string, skillIndex: number) => (
                                <span
                                  key={skillIndex}
                                  className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm border border-primary/30"
                                >
                                  {skill}
                                 </span>
                               ))}
                            </div>
                            <Button
                              variant="outline"
                              className="glass-card border-secondary/30 hover:border-secondary/50 px-6 py-2"
                              onClick={() => handleChat(candidate.id)}
                            >
                              Chat
                            </Button>
                          </div>

                          <div className="flex flex-col items-center gap-2">

                            <div className="relative w-16 h-16">
                              <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                  className="text-muted/20"
                                  stroke="currentColor"
                                  strokeWidth="3"
                                  fill="none"
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path
                                  className="text-primary"
                                  stroke="currentColor"
                                  strokeWidth="3"
                                  strokeDasharray={`${candidate.score}, 100`}
                                  strokeLinecap="round"
                                  fill="none"
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                              </svg>
                              <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-primary">
                                {candidate.score}%
                              </span>
                            </div>
                            <span className="text-xs text-muted-foreground">Match Score</span>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
               <Card className="glass-card p-8 text-center">
                <p className="text-muted-foreground">No matching resumes found for the given criteria. Try adjusting the similarity threshold.</p>
              </Card>
            )}
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default ResumeMatchingDashboard;
