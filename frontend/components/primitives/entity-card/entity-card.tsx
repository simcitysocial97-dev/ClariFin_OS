/**
 * Entity Card - Stage 8C Financial OS Visual System
 *
 * Displays financial entity information.
 */

'use client';

import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';

// ===== Props =====
interface EntityCardProps {
  id: string;
  label: string;
  valuePaise?: number;
  subtitle?: string;
  status?: string;
  confidence?: number;
  onClick?: () => void;
  className?: string;
}

// ===== Entity Card Component =====
export function EntityCard({
  label,
  valuePaise,
  subtitle,
  status,
  onClick,
  className,
}: EntityCardProps) {
  return (
    <div
      className={cn(
        'p-3 border rounded-md hover:bg-gray-50 cursor-pointer transition-colors',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium">{label}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {valuePaise !== undefined && (
          <p className="text-sm font-mono font-medium">{formatINR(valuePaise)}</p>
        )}
      </div>
      {status && (
        <p className="text-xs text-gray-400 mt-2">{status}</p>
      )}
    </div>
  );
}