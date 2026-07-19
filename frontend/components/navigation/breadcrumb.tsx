/**
 * Breadcrumb Component - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation breadcrumb showing current location in the workspace.
 * Responsive design for mobile and desktop.
 * Dark mode support with bg-background classes.
 * Accessibility with proper ARIA attributes.
 */

'use client';

import { ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

/**
 * Breadcrumb Component
 * Displays navigation path with clickable items
 * Responsive: wraps on mobile, horizontal on desktop
 * Dark mode: uses text-muted-foreground for proper theme support
 * Accessibility: includes aria-label and navigation role
 */
export function Breadcrumb({ items, className }: BreadcrumbProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <nav
      className={cn(
        'flex items-center flex-wrap text-sm text-muted-foreground',
        'px-4 py-2 bg-background dark:bg-background',
        className
      )}
      aria-label="Breadcrumb navigation"
      role="navigation"
    >
      <ol className="flex items-center flex-wrap">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight
                  className="h-4 w-4 mx-1 text-muted-foreground/50"
                  aria-hidden="true"
                />
              )}

              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="flex items-center hover:text-foreground transition-colors"
                  aria-label={`Navigate to ${item.label}`}
                >
                  {index === 0 && <Home className="h-4 w-4 mr-1" aria-hidden="true" />}
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span
                  className={cn(
                    'flex items-center',
                    isLast ? 'text-foreground font-medium' : 'text-muted-foreground'
                  )}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {index === 0 && <Home className="h-4 w-4 mr-1" aria-hidden="true" />}
                  <span>{item.label}</span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}