"use client";

/**
 * Bento Grid Layout
 * =================
 * 
 * Responsive 12-column grid layout for dashboard widgets.
 * Provides consistent spacing and responsive behavior across all breakpoints.
 */

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface BentoGridLayoutProps {
  children: ReactNode;
  className?: string;
}

export function BentoGridLayout({ children, className }: BentoGridLayoutProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-4",
        className
      )}
    >
      {children}
    </div>
  );
}

interface BentoGridItemProps {
  children: ReactNode;
  colSpan?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  className?: string;
}

export function BentoGridItem({ 
  children, 
  colSpan = 4,
  className 
}: BentoGridItemProps) {
  const colSpanClasses: Record<number, string> = {
    1: "lg:col-span-1",
    2: "lg:col-span-2",
    3: "lg:col-span-3",
    4: "lg:col-span-4",
    5: "lg:col-span-5",
    6: "lg:col-span-6",
    7: "lg:col-span-7",
    8: "lg:col-span-8",
    9: "lg:col-span-9",
    10: "lg:col-span-10",
    11: "lg:col-span-11",
    12: "lg:col-span-12",
  };

  return (
    <div className={cn(colSpanClasses[colSpan], className)}>
      {children}
    </div>
  );
}
