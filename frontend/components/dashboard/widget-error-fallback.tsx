"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface WidgetErrorFallbackProps {
  title: string;
  error: string;
  onRetry?: () => void;
}

export function WidgetErrorFallback({ title, error, onRetry }: WidgetErrorFallbackProps) {
  return (
    <Card className="h-[320px]">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-red-600">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center h-[250px] text-center px-6">
        <AlertCircle className="h-10 w-10 text-red-500/50 mb-3" />
        <p className="text-muted-foreground text-sm">Error loading data</p>
        <p className="text-muted-foreground text-xs mt-1 max-w-full truncate">
          {error}
        </p>
        {onRetry && (
          <Button 
            variant="outline" 
            size="sm" 
            className="mt-4"
            onClick={onRetry}
          >
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
}