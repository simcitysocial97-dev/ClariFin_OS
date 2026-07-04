"use client";

/**
 * Widget Error Fallback
 * =====================
 * 
 * Standardized error UI for failed dashboard widgets.
 * Provides retry functionality and graceful degradation.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface WidgetErrorFallbackProps {
  title?: string;
  error?: string;
  onRetry?: () => void;
}

export function WidgetErrorFallback({ 
  title = "Failed to load", 
  error = "Something went wrong",
  onRetry 
}: WidgetErrorFallbackProps) {
  return (
    <Card className="h-full border-destructive/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-destructive flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{error}</p>
        {onRetry && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onRetry}
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
