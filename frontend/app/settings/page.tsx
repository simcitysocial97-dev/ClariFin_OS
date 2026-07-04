'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageShell } from '@/components/layout/page-shell';
import { SectionCard } from '@/components/ui/section-card';
import { useCategories } from '@/lib/hooks/use-finance-data';
import { Plus, Trash2, Upload, Download, FileJson } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <PageShell title="Settings" subtitle="Application preferences">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
          <TabsTrigger value="income">Income</TabsTrigger>
          <TabsTrigger value="backup">Backup</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <SectionCard title="Display">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label htmlFor="theme">Theme</Label><Select defaultValue="system"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="light">Light</SelectItem><SelectItem value="dark">Dark</SelectItem><SelectItem value="system">System</SelectItem></SelectContent></Select></div>
                <div><Label htmlFor="currency">Currency</Label><Input id="currency" defaultValue="INR" /></div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label htmlFor="fiscal_year">Fiscal Year Start</Label><Select defaultValue="april"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="april">April</SelectItem><SelectItem value="january">January</SelectItem></SelectContent></Select></div>
                <div><Label htmlFor="locale">Locale</Label><Input id="locale" defaultValue="en-IN" /></div>
              </div>
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <SectionCard title="Categories" subtitle="Manage transaction categories">
            <div className="space-y-3">
              <CategoryManager />
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="income" className="space-y-4">
          <SectionCard title="Income Sources" subtitle="Manage your income streams">
            <div className="space-y-3">
              <IncomeManager />
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="backup" className="space-y-4">
          <SectionCard title="Data Export">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div><p className="text-sm font-medium">Export all data (JSON)</p><p className="text-xs text-muted-foreground">Full backup including transactions, accounts, loans, cards</p></div>
                <Button variant="outline"><FileJson className="h-4 w-4 mr-2" />Export</Button>
              </div>
              <div className="flex items-center justify-between">
                <div><p className="text-sm font-medium">Export transactions (CSV)</p><p className="text-xs text-muted-foreground">Transaction history only</p></div>
                <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
              </div>
              <div className="flex items-center justify-between">
                <div><p className="text-sm font-medium">Import backup</p><p className="text-xs text-muted-foreground">Restore from JSON backup</p></div>
                <Button variant="outline"><Upload className="h-4 w-4 mr-2" />Import</Button>
              </div>
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          <SectionCard title="Advanced">
            <div className="space-y-3">
              <div><Label>Database Path</Label><Input readOnly defaultValue="/data/finance.db" className="font-mono text-xs" /></div>
              <div><Label>App Version</Label><Input readOnly defaultValue="1.0.0" /></div>
              <div className="pt-2">
                <Button variant="destructive">Reset All Data</Button>
              </div>
            </div>
          </SectionCard>
        </TabsContent>
      </Tabs>
    </PageShell>
  );
}

// ============================================================
// Category Manager (stub)
// ============================================================

function CategoryManager() {
  const { data: categoriesData } = useCategories();
  const cats = categoriesData?.summary ?? [];
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-muted-foreground">{cats.length} categories</p>
        <Button size="sm"><Plus className="h-3.5 w-3.5 mr-1.5" />Add</Button>
      </div>
      <div className="space-y-1">
        {cats.map((c) => (
          <div key={c.category} className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm">
            <span>{c.category}</span>
            <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4 text-red-500" /></Button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// Income Manager (stub)
// ============================================================

function IncomeManager() {
  const [items] = useState<{ id: number; name: string; amount: number; frequency: string }[]>([
    { id: 1, name: 'Salary', amount: 500000, frequency: 'monthly' },
  ]);
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-muted-foreground">{items.length} sources</p>
        <Button size="sm"><Plus className="h-3.5 w-3.5 mr-1.5" />Add</Button>
      </div>
      <div className="space-y-1">
        {items.map((item) => (
          <div key={item.id} className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm">
            <div><p className="font-medium">{item.name}</p><p className="text-xs text-muted-foreground">{item.frequency} • ₹{item.amount.toLocaleString()}</p></div>
            <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4 text-red-500" /></Button>
          </div>
        ))}
      </div>
    </div>
  );
}