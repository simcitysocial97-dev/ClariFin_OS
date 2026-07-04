import {
  LayoutDashboard,
  ArrowUpDown,
  Building2,
  CreditCard,
  Landmark,
  TrendingUp,
  Settings,
} from 'lucide-react';

export interface NavItem {
  name: string;
  href: string;
  icon: any;
  description?: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

// CORE ROUTES - These appear in primary navigation
export const CORE_NAV_SECTIONS: NavSection[] = [
  {
    title: 'Overview',
    items: [
      {
        name: 'Dashboard',
        href: '/dashboard',
        icon: LayoutDashboard,
        description: 'Financial health snapshot',
      },
    ],
  },
  {
    title: 'Manage',
    items: [
      {
        name: 'Transactions',
        href: '/transactions',
        icon: ArrowUpDown,
        description: 'Transaction workspace',
      },
      {
        name: 'Accounts',
        href: '/accounts',
        icon: Building2,
        description: 'Bank accounts',
      },
      {
        name: 'Credit Cards',
        href: '/cards',
        icon: CreditCard,
        description: 'Card management',
      },
      {
        name: 'Loans',
        href: '/loans',
        icon: Landmark,
        description: 'Loan tracking',
      },
      {
        name: 'Investments',
        href: '/investments',
        icon: TrendingUp,
        description: 'Portfolio',
      },
    ],
  },
];

// SETTINGS ROUTE - Appears in footer
export const SETTINGS_NAV: NavItem = {
  name: 'Settings',
  href: '/settings',
  icon: Settings,
  description: 'App preferences and data',
};

// DEPRECATED ROUTES - Redirect to new locations
export const ROUTE_REDIRECTS: Record<string, string> = {
  '/import': '/transactions?tab=import',
  '/imports': '/transactions?tab=import',
  '/statements': '/transactions?tab=statements',
  '/reconciliation': '/transactions?tab=reconcile',
  '/categories': '/settings?tab=categories',
  '/income': '/settings?tab=income',
  '/income-sources': '/settings?tab=income',
  '/export': '/settings?tab=backup',
  '/snapshots': '/dashboard?view=history',
  '/networth': '/dashboard?view=networth',
  '/cashflow': '/dashboard?view=cashflow',
  '/analytics': '/dashboard?view=analytics',
  '/projections': '/loans?tab=simulator',
  '/recurring': '/transactions?filter=recurring',
  '/audit': '/settings?tab=advanced',
  '/behavior': '/settings?tab=advanced',
};

// ALLOWED ROUTES - Prevent 404s for valid paths
export const ALLOWED_ROUTES = [
  ...CORE_NAV_SECTIONS.flatMap(section => section.items.map(item => item.href)),
  SETTINGS_NAV.href,
  ...Object.keys(ROUTE_REDIRECTS),
];