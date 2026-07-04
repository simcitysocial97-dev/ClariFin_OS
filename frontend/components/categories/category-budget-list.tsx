'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wallet, CalendarDays, TrendingUp, Bell } from 'lucide-react';

/**
 * Category Budget List - Coming Soon
 * 
 * This component will allow users to:
 * - Set monthly budgets for each spending category
 * - Track spending against budgets in real-time
 * - Receive alerts when approaching budget limits
 * - View historical budget performance
 * 
 * Backend API needed:
 * - GET /api/budgets - List category budgets
 * - POST /api/budgets - Create budget
 * - PUT /api/budgets/:id - Update budget
 * - DELETE /api/budgets/:id - Delete budget
 */
export function CategoryBudgetList() {
  const features = [
    { icon: Wallet, label: 'Set monthly budgets per category' },
    { icon: TrendingUp, label: 'Track spending vs budget' },
    { icon: Bell, label: 'Budget limit alerts' },
    { icon: CalendarDays, label: 'Monthly budget reports' },
  ];

  return (
    <Card className="border-dashed border-2 bg-muted/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Wallet className="h-5 w-5 text-muted-foreground" />
            Monthly Budget Overview
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Coming Soon
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Set and track budgets for each spending category
        </p>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div
              key={feature.label}
              className="flex items-center gap-3 p-3 rounded-lg bg-background/50 border"
            >
              <feature.icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="text-sm text-muted-foreground">{feature.label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
