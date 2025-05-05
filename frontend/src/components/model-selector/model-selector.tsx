'use client';

import { useState, useEffect } from 'react';
import { Check, ChevronDown, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface Model {
  name: string;
  size: number;
  modified_at: string;
  details: Record<string, any>;
}

export default function ModelSelector() {
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin;
      const response = await fetch(`${apiUrl}/api/models`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }
      const data = await response.json();
      setModels(data.models || []);
      setCurrentModel(data.current_model || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch models');
      console.error('Error fetching models:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Select a model
  const selectModel = async (modelName: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin;
      const response = await fetch(`${apiUrl}/api/models/select`, {
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
      setIsOpen(false);
    } catch (err) {
      toast.error('Failed to select model', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  // Load models on component mount
  useEffect(() => {
    fetchModels();
  }, []);

  // Get model type label
  const getModelTypeLabel = (modelName: string) => {
    if (modelName.includes('coder')) return 'Coding';
    if (modelName.includes('mixtral')) return 'Reasoning';
    if (modelName.includes('llama3')) return 'Creative';
    return 'General';
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md bg-background hover:bg-accent/50 border border-border"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading models...</span>
          </>
        ) : (
          <>
            <span>{currentModel || 'Select Model'}</span>
            <ChevronDown className="h-4 w-4 opacity-50" />
          </>
        )}
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-72 rounded-md shadow-lg bg-popover border border-border">
          <div className="py-1 max-h-60 overflow-auto">
            {error ? (
              <div className="px-3 py-2 text-sm text-destructive">
                <p>Error loading models</p>
                <p className="text-xs opacity-70">{error}</p>
                <button
                  onClick={fetchModels}
                  className="mt-1 text-xs underline"
                >
                  Try again
                </button>
              </div>
            ) : models.length === 0 ? (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                No models available
              </div>
            ) : (
              models.map((model) => (
                <button
                  key={model.name}
                  className={`w-full text-left px-3 py-2 text-sm flex justify-between items-center ${
                    currentModel === model.name
                      ? 'bg-accent/50 text-accent-foreground'
                      : 'hover:bg-accent/30'
                  }`}
                  onClick={() => selectModel(model.name)}
                >
                  <div>
                    <div className="font-medium">{model.name}</div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <span>{getModelTypeLabel(model.name)}</span>
                      <span>•</span>
                      <span>{formatFileSize(model.size)}</span>
                    </div>
                  </div>
                  {currentModel === model.name && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </button>
              ))
            )}
          </div>
          <div className="border-t border-border p-2">
            <button
              onClick={() => {
                setIsOpen(false);
                window.location.href = '/settings/models';
              }}
              className="w-full text-left px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent/30 rounded"
            >
              Manage models...
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
