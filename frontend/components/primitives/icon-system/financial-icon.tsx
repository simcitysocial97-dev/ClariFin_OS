/**
 * FinancialIcon - Stage 8E Financial OS Visual Language
 *
 * Domain-mapped icon system. Maps financial entity types to Lucide icons.
 * Swap Lucide for any other icon library in one place.
 */

import {
  ArrowDownRight,
  CheckSquare,
  Eye,
  GitBranch,
  LayoutDashboard,
  ArrowRight,
  ArrowLeftRight,
  Banknote,
  Building2,
  Calendar,
  Cog,
  CreditCard,
  DollarSign,
  FileSearch,
  GitCompare,
  HandCoins,
  Home,
  Landmark,
  LineChart,
  PieChart,
  PiggyBank,
  Receipt,
  RefreshCw,
  Scale,
  Search,
  Send,
  Shield,
  ShoppingCart,
  Sparkles,
  TrendingDown,
  TrendingUp,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react';

// ===== Entity → Icon Mapping =====
// Single source of truth. Change icon library here.
const iconMap: Record<string, LucideIcon> = {
  transaction: Receipt,
  'layout-dashboard': LayoutDashboard,
  'check-square': CheckSquare,
  'arrow-left-right': ArrowLeftRight,
  'trending-up': TrendingUp,
  'crystal-ball': Eye,
  wallet: Landmark,
  receipt: Receipt,
  'pie-chart': PieChart,
  brain: Sparkles,
  settings: Cog,
  automate: RefreshCw,
  account: Landmark,
  loan: HandCoins,
  'credit-card': CreditCard,
  investment: TrendingUp,
  behaviour: Sparkles,
  merchant: ShoppingCart,
  category: PieChart,
  institution: Building2,
  forecast: LineChart,
  'net-worth': PiggyBank,
  reconciliation: Scale,
  discrepancy: TriangleAlert,
  search: Search,
  filter: FileSearch,
  sort: ArrowDownRight,
  group: ArrowRight,
  export: Send,
  refresh: RefreshCw,
  simulate: GitCompare,
  rule: Shield,
  warning: TriangleAlert,
  positive: TrendingUp,
  negative: TrendingDown,
  transfer: ArrowLeftRight,
  cashflow: DollarSign,
  date: Calendar,
  salary: Banknote,
  home: Home,
  evidence: FileSearch,
  graph: GitBranch,
};

// ===== Icon Props =====
interface FinancialIconProps {
  name: string;
  className?: string;
  size?: number;
}

export function FinancialIcon({
  name,
  className,
  size = 16,
}: FinancialIconProps) {
  const Icon = iconMap[name] ?? ArrowRight;
  return <Icon className={className} size={size} />;
}

// ===== Direct Icon Access =====
export function getFinancialIcon(name: string): LucideIcon {
  return iconMap[name] ?? ArrowRight;
}

// ===== Export icon names for type safety =====
export type FinancialIconName = keyof typeof iconMap;