import React, { useState, useEffect } from "react";
import { CheckSquare, ListTodo, AlertTriangle, CheckCircle, CircleDashed } from "lucide-react";
import { ToolViewProps } from "./types";
import { extractFilePath, extractFileContent } from "./utils";
import { GenericToolView } from "./GenericToolView";
import { MarkdownRenderer } from "@/components/file-renderers/markdown-renderer";
import { cn } from "@/lib/utils";
import { useParams } from "next/navigation";

export function TodoListView({
  assistantContent,
  toolContent,
  assistantTimestamp,
  toolTimestamp,
  isSuccess = true,
  isStreaming = false,
  name,
  project
}: ToolViewProps) {
  const [todoContent, setTodoContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const params = useParams();
  const projectId = project?.id || params?.projectId as string;

  useEffect(() => {
    const fetchTodoContent = async () => {
      if (!projectId) {
        setError("Project ID not found");
        setIsLoading(false);
        return;
      }

      try {
        // Extract todo content from the tool call if available
        if (toolContent && toolContent.includes("todo.md")) {
          setTodoContent("# Todo List\n\n- [ ] Task created by agent\n- [ ] More tasks will appear here");
          setIsLoading(false);
          return;
        }
        
        // If assistant content mentions todo, extract it
        if (assistantContent && assistantContent.toLowerCase().includes("todo")) {
          const todoMatch = assistantContent.match(/```md([\s\S]*?)```/);
          if (todoMatch && todoMatch[1]) {
            setTodoContent(todoMatch[1]);
            setIsLoading(false);
            return;
          }
        }
        
        // Default content if we can't extract it
        setTodoContent("Todo list will appear here when the agent creates it.");
        setIsLoading(false);
      } catch (err) {
        setError(`Error processing todo list: ${err instanceof Error ? err.message : String(err)}`);
        setIsLoading(false);
      }
    };

    fetchTodoContent();
  }, [projectId, assistantContent, toolContent]);

  // If this is not a todo-related tool call, use the generic view
  if (!name?.toLowerCase().includes("todo")) {
    return (
      <GenericToolView
        assistantContent={assistantContent}
        toolContent={toolContent}
        assistantTimestamp={assistantTimestamp}
        toolTimestamp={toolTimestamp}
        isSuccess={isSuccess}
        isStreaming={isStreaming}
        name={name}
        project={project}
      />
    );
  }

  return (
    <div className="flex flex-col space-y-2 w-full">
      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
        <ListTodo className="h-4 w-4" />
        <span>Todo List</span>
        {assistantTimestamp && (
          <span className="text-xs opacity-50">
            {new Date(assistantTimestamp).toLocaleTimeString()}
          </span>
        )}
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
          <div className="prose dark:prose-invert max-w-none">
            {todoContent && <MarkdownRenderer content={todoContent} />}
          </div>
        )}
      </div>

      {/* Display the tool result if available */}
      {toolContent && (
        <div className="mt-2 text-sm">
          <div className="flex items-center space-x-2 text-muted-foreground mb-1">
            {isSuccess ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            )}
            <span>{isSuccess ? "Todo list updated" : "Failed to update todo list"}</span>
            {toolTimestamp && (
              <span className="text-xs opacity-50">
                {new Date(toolTimestamp).toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className={cn("text-sm p-2 rounded-md", isSuccess ? "bg-muted/50" : "bg-destructive/10")}>
            {toolContent}
          </div>
        </div>
      )}
    </div>
  );
}
