/**
 * Entity Card - Stage 8E Financial OS Visual Language
 *
 * Displays financial entity information.
 * Built on Surface primitive for unified visual language.
 */

'use client';

import { formatINR } from '@/lib/utils/format';
import { cn } from '@/lib/utils';
import { Surface } from '@/components/primitives/surface/surface';

interface EntityCardProps {
  id: string;
  label: string;
  valuePaise?: number;
  subtitle?: string;
  status?: string;
  onClick?: () => void;
  className?: string;
}

export function EntityCard({
  label,
  valuePaise,
  subtitle,
  status,
  onClick,
  className,
}: EntityCardProps) {
  return (
    <Surface
      variant={onClick ? 'interactive' : 'raised'}
      density="default"
      radius="md"
      className={cn('cursor-pointer', className)}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="fin-label text-[var(--text-primary)] truncate">{label}</p>
          {subtitle && (
            <p className="fin-caption text-[var(--text-tertiary)] mt-1 truncate">{subtitle}</p>
          )}
        </div>
        {valuePaise !== undefined && (
          <p className="fin-amount text-[var(--text-primary)] font-medium ml-2 shrink-0">
            {formatINR(valuePaise)}
          </p>
        )}
      </div>
      {status && (
        <p className="fin-caption text-[var(--text-tertiary)] mt-2 truncate">{status}</p>
      )}
    </Surface>
  );
}
