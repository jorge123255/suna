'use client';

import { useEffect, useState } from 'react';
import ModelManagement from '@/components/model-management/model-management';

export default function ModelsSettingsPage() {
  const [apiUrl, setApiUrl] = useState('');

  useEffect(() => {
    // Get the API URL from the environment or use a default
    const url = process.env.NEXT_PUBLIC_API_URL || window.location.origin;
    setApiUrl(url);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Model Management</h3>
        <p className="text-sm text-muted-foreground">
          Manage the LLM models used by your agent for reasoning and task execution
        </p>
      </div>
      
      {apiUrl && <ModelManagement apiUrl={apiUrl} />}
    </div>
  );
}
