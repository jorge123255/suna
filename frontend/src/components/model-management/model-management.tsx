'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Check, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface Model {
  name: string;
  size: number;
  modified_at: string;
  details: Record<string, any>;
}

interface ModelManagementProps {
  apiUrl: string;
}

export default function ModelManagement({ apiUrl }: ModelManagementProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingModel, setDownloadingModel] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Format file size in a human-readable format
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Fetch available models
  const fetchModels = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/models`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }
      const data = await response.json();
      setModels(data.models || []);
      setCurrentModel(data.current_model || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch models');
      toast.error('Failed to fetch models', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Select a model
  const selectModel = async (modelName: string) => {
    try {
      const response = await fetch(`${apiUrl}/models/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_name: modelName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select model');
      }

      const data = await response.json();
      setCurrentModel(modelName);
      toast.success('Model selected', {
        description: `Now using ${modelName} for inference`,
      });
    } catch (err) {
      toast.error('Failed to select model', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  // Download a model
  const downloadModel = async (modelName: string) => {
    setDownloadingModel(modelName);
    setDownloadProgress(0);
    
    try {
      const response = await fetch(`${apiUrl}/models/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_name: modelName }),
      });

      if (!response.ok) {
        throw new Error(`Failed to download model: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      // Process the streaming response
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Convert the chunk to text
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            const progress = JSON.parse(line);
            
            if (progress.error) {
              throw new Error(progress.error);
            }

            // Update progress based on completed/total
            if (progress.completed && progress.total) {
              const percentage = (progress.completed / progress.total) * 100;
              setDownloadProgress(percentage);
            }
            
            // If download is complete
            if (progress.status === 'success') {
              toast.success('Model downloaded successfully', {
                description: `${modelName} is now available for use`,
              });
              // Refresh the model list
              fetchModels();
            }
          } catch (err) {
            console.error('Error parsing progress:', err);
          }
        }
      }
    } catch (err) {
      toast.error('Failed to download model', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    } finally {
      setDownloadingModel(null);
      setDownloadProgress(0);
    }
  };

  // Load models on component mount
  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Model Management</CardTitle>
        <CardDescription>
          Manage the LLM models used by the agent for reasoning and task execution
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="bg-destructive/10 p-4 rounded-md flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-destructive">Error loading models</p>
              <p className="text-sm text-muted-foreground">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2"
                onClick={fetchModels}
              >
                Try Again
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-4">
              {models.map((model) => (
                <div
                  key={model.name}
                  className={`p-4 rounded-lg border ${
                    currentModel === model.name ? 'border-primary bg-primary/5' : 'border-border'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{model.name}</h3>
                        {currentModel === model.name && (
                          <Badge variant="outline" className="bg-primary/10 text-primary">
                            Current
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        Size: {formatFileSize(model.size)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {downloadingModel === model.name ? (
                        <div className="w-24">
                          <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary" 
                              style={{ width: `${downloadProgress}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-center mt-1">{Math.round(downloadProgress)}%</p>
                        </div>
                      ) : (
                        <Button
                          variant={currentModel === model.name ? "secondary" : "default"}
                          size="sm"
                          onClick={() => selectModel(model.name)}
                          disabled={currentModel === model.name || !!downloadingModel}
                        >
                          {currentModel === model.name ? (
                            <>
                              <Check className="h-4 w-4 mr-1" /> Selected
                            </>
                          ) : (
                            'Select'
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="pt-4 border-t">
              <h3 className="font-medium mb-2">Download New Model</h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                {['llama3:8b', 'mixtral:8x22b-instruct-v0.1-q4_K_M', 'qwen2.5-coder:32b-instruct-q8_0', 'qwen2.5:32b-instruct-q4_K_M'].map((modelName) => (
                  <Button
                    key={modelName}
                    variant="outline"
                    className="h-auto py-2 px-3 justify-start"
                    disabled={!!downloadingModel || models.some(m => m.name === modelName)}
                    onClick={() => downloadModel(modelName)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    <div className="text-left">
                      <div className="text-sm font-medium">{modelName}</div>
                      <div className="text-xs text-muted-foreground">
                        {modelName.includes('coder') ? 'Coding' : 
                         modelName.includes('mixtral') ? 'Reasoning' :
                         modelName.includes('llama3') ? 'Creative' : 'General'}
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
              
              {downloadingModel && (
                <div className="mt-4 p-3 border rounded-md">
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <p className="text-sm font-medium">Downloading {downloadingModel}</p>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary" 
                      style={{ width: `${downloadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {Math.round(downloadProgress)}% complete
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between border-t pt-6">
        <Button variant="outline" onClick={fetchModels} disabled={isLoading || !!downloadingModel}>
          Refresh
        </Button>
      </CardFooter>
    </Card>
  );
}
