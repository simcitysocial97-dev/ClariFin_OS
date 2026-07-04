'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tag, Sparkles, Filter, Zap, List } from 'lucide-react';

/**
 * Merchant Rules Table - Coming Soon
 * 
 * This component will allow users to:
 * - Create pattern-based auto-categorization rules
 * - Match transaction descriptions to categories
 * - View rule match statistics
 * - Bulk-categorize based on rules
 * 
 * Backend API needed:
 * - GET /api/merchant-rules - List rules
 * - POST /api/merchant-rules - Create rule
 * - PUT /api/merchant-rules/:id - Update rule
 * - DELETE /api/merchant-rules/:id - Delete rule
 * - POST /api/merchant-rules/apply - Apply rules to uncategorized
 */
export function MerchantRulesTable() {
  const features = [
    { icon: Tag, label: 'Pattern-based auto-categorization' },
    { icon: Filter, label: 'Custom description matching' },
    { icon: Zap, label: 'Bulk apply to transactions' },
    { icon: List, label: 'Rule statistics & history' },
  ];

  return (
    <Card className="border-dashed border-2 bg-muted/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-muted-foreground" />
            Auto-Categorization Rules
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Coming Soon
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Create rules to automatically categorize transactions based on description patterns
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
