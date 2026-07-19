/**
 * Back Button Component - Stage 3 Transaction Intelligence Workspace
 *
 * Navigation back button for returning to previous view.
 * Responsive design for mobile and desktop.
 * Dark mode support with bg-background classes.
 * Accessibility with proper ARIA attributes.
 */

'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface BackButtonProps {
  label?: string;
  fallbackHref?: string;
  className?: string;
}

/**
 * Back Button Component
 * Navigates back in browser history or to fallback URL
 * Responsive: full width on mobile, auto on desktop
 * Dark mode: uses bg-background for proper theme support
 * Accessibility: includes aria-label and button role
 */
export function BackButton({
  label = 'Back',
  fallbackHref = '/transactions',
  className,
}: BackButtonProps) {
  const router = useRouter();

  const handleBack = () => {
    // Try to go back in history, fallback to fallbackHref if no history
    if (typeof window !== 'undefined' && window.history.length > 1) {
      router.back();
    } else {
      router.push(fallbackHref);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleBack}
      className={cn(
        'flex items-center gap-2 px-2',
        'hover:bg-accent hover:text-accent-foreground',
        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        className
      )}
      aria-label={`Go back to previous page`}
    >
      <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      <span className="hidden sm:inline">{label}</span>
    </Button>
  );
}