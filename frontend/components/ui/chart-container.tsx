import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3 } from "lucide-react";

interface ChartContainerProps {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
  title?: string;
}

export function ChartContainer({
  isLoading,
  isError,
  isEmpty,
  emptyMessage = "No data available",
  onRetry,
  children,
  title,
}: ChartContainerProps) {
  // Loading state - render skeleton matching chart height
  if (isLoading) {
    return (
      <div className="w-full">
        {title && (
          <div className="mb-3">
            <Skeleton className="h-5 w-32" />
          </div>
        )}
        <Skeleton className="h-[200px] w-full rounded-lg" />
      </div>
    );
  }

  // Error state - render error message with retry option
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-[200px] text-center px-4">
        <p className="text-sm text-muted-foreground mb-2">Unable to load chart data</p>
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

  // Empty state - render empty message with chart icon
  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center h-[200px] text-center px-4">
        <BarChart3 className="h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  // Render children (the actual chart)
  return <>{children}</>;
}