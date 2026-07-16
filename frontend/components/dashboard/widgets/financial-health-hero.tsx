/**
 * Financial Health Hero Widget - Conversation-first financial health display
 * 
 * Shows health score with conversational context instead of just numbers.
 */

'use client';
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useDashboardMetrics } from '@/lib/hooks/use-dashboard-metrics';

interface HealthSignal {
  type: 'positive' | 'warning' | 'critical';
  label: string;
  value: string;
}

function getHealthStatus(score: number): { label: string; color: string } {
  if (score >= 70) return { label: 'Healthy', color: 'text-green-600' };
  if (score >= 40) return { label: 'Manageable', color: 'text-amber-600' };
  return { label: 'Needs Attention', color: 'text-red-600' };
}

function getTrendIcon(value: string): React.ReactNode {
  if (value.startsWith('+')) {
    return <TrendingUp className="h-3 w-3 text-green-500" />;
  }
  return <TrendingDown className="h-3 w-3 text-red-500" />;
}

export function FinancialHealthHero() {
  const { data } = useDashboardMetrics();

  if (!data) return null;

  const healthStatus = getHealthStatus(data.financial_health_score);
  const signals: HealthSignal[] = [
    { type: 'positive', label: 'Cashflow improved', value: '+12%' },
    { type: 'positive', label: 'Savings improved', value: '+₹12,400' },
    { type: 'warning', label: 'EMI ratio increased', value: '◀ 38% from 35%' },
  ];

  const todayFocus = {
    action: 'Increase emergency fund',
    amount: '₹8,000',
    impact: 4,
  };

  return (
    <div className="space-y-4">
      {/* Health Score Hero */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <h2 className="text-sm text-muted-foreground mb-1">Financial Health</h2>
          <div className="flex items-baseline gap-3">
            <span className="text-4xl font-bold">{data.financial_health_score}</span>
            <span className={`text-lg ${healthStatus.color}`}>{healthStatus.label}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-sm">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <span>+5 from last month</span>
          </div>
        </div>
      </div>

      {/* Health Signals */}
      <div className="space-y-2">
        {signals.map((signal, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            {signal.type === 'positive' && <CheckCircle2 className="h-3 w-3 text-green-500" />}
            {signal.type === 'warning' && <AlertCircle className="h-3 w-3 text-amber-500" />}
            <span className="text-muted-foreground">{signal.label}</span>
            <span className="ml-auto font-medium flex items-center gap-1">
              {getTrendIcon(signal.value)}
              {signal.value}
            </span>
          </div>
        ))}
      </div>

      {/* Today's Focus */}
      <div className="border-t pt-3">
        <p className="text-xs text-muted-foreground mb-2">TODAY'S FOCUS</p>
        <div className="space-y-1">
          <p className="font-medium">{todayFocus.action} by {todayFocus.amount}</p>
          <div className="flex items-center gap-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded ${
                  i < todayFocus.impact ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}