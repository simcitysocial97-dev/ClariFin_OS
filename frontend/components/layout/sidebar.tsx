'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { ThemeToggle } from '@/components/theme-toggle';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { cn } from '@/lib/utils';
import { formatINRCompact } from '@/lib/utils/format';
import { useNetWorth } from '@/lib/hooks/use-finance-data';
import { Settings, Menu, ChevronLeft, ChevronRight, Wallet } from 'lucide-react';
import { CORE_NAV_SECTIONS } from '@/lib/config/navigation';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  section: string;
  items: NavItem[];
}

// Convert centralized config to sidebar format
const NAV_ITEMS: NavSection[] = CORE_NAV_SECTIONS.map(section => ({
  section: section.title.toUpperCase(),
  items: section.items.map(item => ({
    label: item.name,
    href: item.href,
    icon: item.icon,
  })),
}));

interface SidebarProps {
  sidebarCollapsed?: boolean;
  toggleSidebar?: () => void;
}

export function Sidebar({ sidebarCollapsed = false, toggleSidebar }: SidebarProps) {
  const pathname = usePathname();
  const { data: netWorthData } = useNetWorth();
  const netWorthPaise = netWorthData?.net_worth_paise ?? 0;
  const netWorthDisplay = formatINRCompact(netWorthPaise);
  const isPositive = netWorthPaise >= 0;

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2">
          <Wallet className="h-5 w-5" />
          {!sidebarCollapsed && <span className="font-semibold">ClariFin</span>}
        </Link>
      </div>

      {/* Net Worth Chip */}
      <div className="px-3 py-4 border-b">
        <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-3 py-2">
          <Wallet className="h-4 w-4 text-muted-foreground" />
          {!sidebarCollapsed ? (
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                Net Worth
              </span>
              <span className={cn('text-sm font-semibold', isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400')}>
                {netWorthDisplay}
              </span>
            </div>
          ) : (
            <span className={cn('text-sm font-semibold', isPositive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400')}>
              {netWorthDisplay}
            </span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3">
        <nav className="flex flex-col gap-5">
          {NAV_ITEMS.map((section) => (
            <div key={section.section} className="flex flex-col gap-1">
              {!sidebarCollapsed && (
                <p className="px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                  {section.section}
                </p>
              )}
              <div className="flex flex-col gap-0.5">
                {section.items.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      )}
                    >
                      <item.icon className="h-4 w-4 flex-shrink-0" />
                      {!sidebarCollapsed && <span>{item.label}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* Footer */}
      <div className="border-t p-3">
        <div className="flex flex-col gap-2">
          {toggleSidebar && (
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="hidden lg:flex justify-start gap-2"
            >
              {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              {!sidebarCollapsed && <span>Collapse</span>}
            </Button>
          )}
          <Link
            href="/settings"
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              pathname === '/settings'
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <Settings className="h-4 w-4 flex-shrink-0" />
            {!sidebarCollapsed && <span>Settings</span>}
          </Link>
          <div className="flex items-center justify-between rounded-lg px-3 py-2">
            {!sidebarCollapsed && (
              <span className="text-sm text-muted-foreground">Theme</span>
            )}
            <ThemeToggle />
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile */}
      <Sheet>
        <SheetTrigger asChild className="lg:hidden">
          <Button variant="ghost" size="icon" className="fixed top-4 left-4 z-50">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0">
          <VisuallyHidden>
            <SheetTitle>Navigation</SheetTitle>
          </VisuallyHidden>
          <SidebarContent />
        </SheetContent>
      </Sheet>

      {/* Desktop */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 hidden h-screen border-r bg-background transition-all duration-300 lg:flex lg:flex-col',
          sidebarCollapsed ? 'w-14' : 'w-56'
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}