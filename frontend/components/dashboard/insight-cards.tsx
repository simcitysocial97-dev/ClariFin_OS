'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import * as LucideIcons from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface Insight {
  title: string;
  description: string;
  severity: 'positive' | 'warning' | 'info' | 'alert';
  icon: string;
}

interface InsightCardsProps {
  insights: Insight[];
}

// Map severity to border color
const severityBorderColors = {
  alert: 'border-l-destructive',
  warning: 'border-l-amber-500',
  info: 'border-l-blue-500',
  positive: 'border-l-green-500',
};

// Map severity to icon color
const severityIconColors = {
  alert: 'text-destructive',
  warning: 'text-amber-500',
  info: 'text-blue-500',
  positive: 'text-green-500',
};

export function InsightCards({ insights }: InsightCardsProps) {
  if (!insights || insights.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {insights.map((insight, index) => {
        // Dynamically get the icon component
        const iconName = insight.icon as keyof typeof LucideIcons;
        const IconComponent = (LucideIcons[iconName] as LucideIcon) || LucideIcons.Info;

        return (
          <Card
            key={index}
            className={cn(
              'border-l-4 transition-shadow hover:shadow-md',
              severityBorderColors[insight.severity]
            )}
          >
            <CardContent className="flex items-start gap-4 p-4">
              <div className={cn('mt-0.5 shrink-0', severityIconColors[insight.severity])}>
                <IconComponent className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h4 className="font-semibold text-sm">{insight.title}</h4>
                <p className="text-sm text-muted-foreground">{insight.description}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
