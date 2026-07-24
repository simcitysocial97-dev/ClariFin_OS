import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3 } from "lucide-react";

interface DataStateWrapperProps {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}

export function DataStateWrapper({
  isLoading,
  isError,
  isEmpty,
  emptyMessage = "No data available",
  onRetry,
  children,
}: DataStateWrapperProps) {
  // Loading state - render skeleton
  if (isLoading) {
    return (
      <div className="w-full">
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
    );
  }

  // Error state - render error message with retry option
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-12 text-center px-4">
        <p className="text-sm text-muted-foreground mb-2">Unable to load data</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-xs text-primary hover:underline"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  // Empty state - render empty message with icon
  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center h-12 text-center px-4">
        <BarChart3 className="h-6 w-6 text-muted-foreground/50 mb-1" />
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  // Render children (the actual content)
  return <>{children}</>;
}