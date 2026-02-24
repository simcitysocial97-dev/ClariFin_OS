'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/lib/store/use-app-store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import {
  LayoutDashboard,
  CreditCard,
  BarChart3,
  Wallet,
  Settings,
  Menu,
  Plus,
  ChevronLeft,
  ChevronRight,
  FileSpreadsheet,
  PieChart,
  Building2
} from 'lucide-react';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { cn } from '@/lib/utils';
import { MemberSelector } from '@/components/members/MemberSelector';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Transactions', href: '/transactions', icon: CreditCard },
  { name: 'Accounts', href: '/accounts', icon: Building2 },
  { name: 'Categories', href: '/categories', icon: PieChart },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Cards', href: '/cards', icon: Wallet },
  { name: 'Import', href: '/import', icon: FileSpreadsheet },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { cards, sidebarCollapsed, toggleSidebar, selectedCardId, selectCard } = useAppStore();

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          <span className="text-2xl">💳</span>
          {!sidebarCollapsed && <span>FinTrack</span>}
        </Link>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="hidden lg:flex"
        >
          {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Upload Button */}
      <div className="p-4">
        <Link href="/?upload=true">
          <Button className="w-full" size={sidebarCollapsed ? 'icon' : 'default'}>
            <Plus className="h-4 w-4" />
            {!sidebarCollapsed && <span className="ml-2">Upload Statement</span>}
          </Button>
        </Link>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3">
        <nav className="flex flex-col gap-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                {!sidebarCollapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Cards Section */}
        {!sidebarCollapsed && cards.length > 0 && (
          <div className="mt-6">
            <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              My Cards
            </h3>
            <div className="mt-2 space-y-1">
              {cards.map((card) => (
                <button
                  key={card.id}
                  onClick={() => selectCard(card.id)}
                  className={cn(
                    'w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors text-left',
                    selectedCardId === card.id
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <span className="text-lg">
                    {getCardStatusIcon(card.dueDate)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{card.bankName}</p>
                    <p className="text-xs text-muted-foreground">
                      •••• {card.cardNumber.slice(-4)}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Member Selector */}
        {!sidebarCollapsed && (
          <div className="mt-6 px-3">
            <MemberSelector showLabel={true} />
          </div>
        )}
      </ScrollArea>
    </div>
  );

  return (
    <>
      {/* Mobile Sidebar */}
      <Sheet>
        <SheetTrigger asChild className="lg:hidden">
          <Button variant="ghost" size="icon" className="fixed top-4 left-4 z-50">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <VisuallyHidden>
            <SheetTitle>Navigation Menu</SheetTitle>
          </VisuallyHidden>
          <SidebarContent />
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300 hidden lg:block',
          sidebarCollapsed ? 'w-16' : 'w-64'
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}

function getCardStatusIcon(dueDate: string): string {
  if (!dueDate) return '⚪';
  const due = new Date(dueDate);
  const today = new Date();
  const daysDiff = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  
  if (daysDiff < 0) return '🔴';
  if (daysDiff <= 3) return '🟡';
  return '🟢';
}
