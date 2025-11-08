import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Users, Eye, Settings, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

const ResumeMatchingDashboard = () => {
  const [previewMode, setPreviewMode] = useState(true);
  const [customerData, setCustomerData] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any[]>([]);

  const handleCustomerDataUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setCustomerData(file);
    }
  };

  const handleAnalysis = async () => {
    if (!customerData) return;

    setIsAnalyzing(true);
    setAnalysisResults([]);

    const formData = new FormData();
    formData.append('file', customerData);

    try {
      const response = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const results = await response.json();
      setAnalysisResults(results);
    } catch (error) {
      console.error("Error during analysis:", error);
      // Optionally, show an error message to the user
    } finally {
      setIsAnalyzing(false);
    }
  };

  const controlSections = [
    {
      title: "Customer Data",
      icon: Users,
      content: (
        <div className="space-y-4">
          <input
            type="file"
            accept=".csv"
            onChange={handleCustomerDataUpload}
            className="hidden"
            id="customer-data-upload"
          />
          <label 
            htmlFor="customer-data-upload"
            className="border-2 border-dashed border-primary/30 rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer block"
          >
            <Upload className="w-8 h-8 text-primary mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              {customerData ? customerData.name : "Upload Customer Data (CSV)"}
            </p>
            {customerData && (
              <p className="text-xs text-primary mt-1">✓ File uploaded</p>
            )}
          </label>
        </div>
      )
    },
    {
      title: "Display Mode",
      icon: Eye,
      content: (
        <div className="flex items-center space-x-2">
          <Switch
            id="preview-mode"
            checked={previewMode}
            onCheckedChange={setPreviewMode}
          />
          <Label htmlFor="preview-mode" className="text-sm">
            {previewMode ? "Preview Mode" : "Full Details"}
          </Label>
        </div>
      )
    }
  ];

  return (
    <section id="dashboard" className="py-20 px-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-muted/5 to-background" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse" />

      <div className="relative z-10 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-gradient-primary">Churn Analysis</span>
            <br />
            <span className="text-gradient-accent">Dashboard</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Upload customer data to predict churn and understand key risk factors using our advanced AI model.
          </p>
        </motion.div>

        {/* Control Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {controlSections.map((section, index) => {
            const IconComponent = section.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
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

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          viewport={{ once: true }}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
        >
          <Button 
            size="lg" 
            className="glass-button neon-glow px-8 py-4 relative overflow-hidden group"
            onClick={handleAnalysis}
            disabled={!customerData || isAnalyzing}
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
                Analyze Customer Data
              </>
            )}
          </Button>
          <Button 
            variant="outline" 
            size="lg" 
            className="glass-card border-secondary/30 hover:border-secondary/50 px-8 py-4"
          >
            <Settings className="mr-2 w-5 h-5" />
            Advanced Settings
          </Button>
        </motion.div>

        {/* Results Section */}
        {analysisResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            viewport={{ once: true }}
            className="space-y-6"
          >
            <h3 className="text-2xl font-bold text-center mb-8">
              <span className="text-gradient-accent">Analysis Results</span>
            </h3>

            <div className="grid gap-6">
              {analysisResults.map((result, index) => (
                <motion.div
                  key={result.id}
                  initial={{ opacity: 0, x: -50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card className="glass-card p-6 hover:shadow-glow-secondary transition-all duration-300 border-l-4 border-l-primary">
                    <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-4 mb-3">
                          <h4 className="text-xl font-semibold">{result.customer_id}</h4>
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                            <span className="text-sm text-muted-foreground">{result.segment}</span>
                          </div>
                        </div>
                        
                        <p className="text-muted-foreground mb-4">Key risk factors:</p>
                        
                        <div className="flex flex-wrap gap-2">
                          {result.risk_factors.map((factor: string, factorIndex: number) => (
                            <span
                              key={factorIndex}
                              className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm border border-primary/30"
                            >
                              {factor}
                            </span>
                          ))}
                        </div>
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
                              strokeDasharray={`${result.churn_probability}, 100`}
                              strokeLinecap="round"
                              fill="none"
                              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                          </svg>
                          <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-primary">
                            {result.churn_probability}%
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">Churn Probability</span>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </section>
  );
};

export default ResumeMatchingDashboard;