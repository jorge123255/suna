import React, { useState, useEffect } from "react";
import { CheckSquare, ListTodo, AlertTriangle, RefreshCw, CircleDashed } from "lucide-react";
import { MarkdownRenderer } from "@/components/file-renderers/markdown-renderer";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface TodoListPanelProps {
  projectId?: string;
  className?: string;
}

export function TodoListPanel({ projectId, className }: TodoListPanelProps) {
  const [todoContent, setTodoContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTodoContent = async () => {
    if (!projectId) {
      setError("Project ID not found");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // In this simplified version, we'll just show a placeholder todo list
      // since we can't access the actual sandbox without Supabase
      setTimeout(() => {
        setTodoContent(`# Agent Todo List

## Initial Research
- [x] Understand the requirements
- [x] Identify key components needed
- [ ] Research best practices and approaches

## Implementation
- [ ] Set up project structure
- [ ] Implement core functionality
- [ ] Add error handling and validation

## Testing
- [ ] Test functionality
- [ ] Fix any bugs
- [ ] Verify requirements are met

## Delivery
- [ ] Clean up code
- [ ] Add documentation
- [ ] Prepare final deliverables`);
        setIsLoading(false);
      }, 500);
    } catch (err) {
      setError(`Error fetching todo list: ${err instanceof Error ? err.message : String(err)}`);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTodoContent();
    
    // Set up polling to refresh the todo list every 10 seconds
    const intervalId = setInterval(fetchTodoContent, 10000);
    
    return () => clearInterval(intervalId);
  }, [projectId]);

  return (
    <div className={cn("flex flex-col space-y-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-sm font-medium">
          <ListTodo className="h-4 w-4" />
          <span>Agent Todo List</span>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={fetchTodoContent} 
          disabled={isLoading}
          className="h-6 w-6"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <div className="rounded-md border p-4 bg-background">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <CircleDashed className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading todo list...</span>
          </div>
        ) : error ? (
          <div className="flex items-center text-destructive py-2">
            <AlertTriangle className="h-4 w-4 mr-2" />
            <span className="text-sm">{error}</span>
          </div>
        ) : (
          <div className="prose dark:prose-invert max-w-none text-sm">
            {todoContent && <MarkdownRenderer content={todoContent} />}
          </div>
        )}
      </div>
    </div>
  );
}
