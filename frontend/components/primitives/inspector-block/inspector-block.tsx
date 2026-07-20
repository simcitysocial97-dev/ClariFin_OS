/**
 * Inspector Block - Stage 8C Financial OS Visual System
 *
 * Reusable inspector section component.
 */

'use client';

import { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// ===== Props =====
interface InspectorBlockProps {
  title: string;
  children: ReactNode;
  className?: string;
  defaultOpen?: boolean;
}

// ===== Inspector Block Component =====
export function InspectorBlock({
  title,
  children,
  className,
}: InspectorBlockProps) {
  return (
    <Card className={cn('m-2 mb-0', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {children}
      </CardContent>
    </Card>
  );
}