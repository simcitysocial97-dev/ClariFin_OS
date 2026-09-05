import { render, screen } from '@testing-library/react';
import { HealthBadge } from '@/components/platform/health-badge';

describe('HealthBadge', () => {
  it('renders with correct status text and dot', () => {
    render(<HealthBadge status="HEALTHY" />);
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    const dot = screen.getByTestId('health-dot');
    expect(dot).toHaveClass('bg-emerald-400');
  });

  it('applies correct variant classes for each status', () => {
    const { rerender } = render(<HealthBadge status="UNHEALTHY" />);
    expect(screen.getByText('UNHEALTHY')).toBeInTheDocument();
    let dot = screen.getByTestId('health-dot');
    expect(dot).toHaveClass('bg-red-400');

    rerender(<HealthBadge status="DEGRAD" />);
    expect(screen.getByText('DEGRAD')).toBeInTheDocument();
    dot = screen.getByTestId('health-dot');
    expect(dot).toHaveClass('bg-amber-400');

    rerender(<HealthBadge status="UNKNOWN" />);
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
    dot = screen.getByTestId('health-dot');
    expect(dot).toHaveClass('bg-slate-400');
  });

  it('renders without label when showLabel is false', () => {
    render(<HealthBadge status="HEALTHY" showLabel={false} />);
    expect(screen.queryByText('HEALTHY')).not.toBeInTheDocument();
  });

  it('applies size classes correctly', () => {
    const { container, rerender } = render(<HealthBadge status="HEALTHY" size="sm" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge).toHaveClass('text-xs');

    rerender(<HealthBadge status="HEALTHY" size="lg" />);
    expect(container.firstChild).toHaveClass('text-sm');
  });

  it('applies custom className', () => {
    render(<HealthBadge status="HEALTHY" className="custom-class" />);
    const badge = screen.getByText('HEALTHY');
    expect(badge).toHaveClass('custom-class');
  });
});