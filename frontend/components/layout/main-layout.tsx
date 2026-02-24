'use client';

import { Sidebar } from './sidebar';
import { useAppStore } from '@/lib/store/use-app-store';
import { cn } from '@/lib/utils';

export function MainLayout({ children }: { children: React.ReactNode }) {
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main
        className={cn(
          'transition-all duration-300 min-h-screen',
          'lg:ml-64',
          sidebarCollapsed && 'lg:ml-16'
        )}
      >
        <div className="container mx-auto p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
