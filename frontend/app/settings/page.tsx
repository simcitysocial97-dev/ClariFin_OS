/**
 * Settings Workspace Page - Configuration surface with runtime registration.
 */

'use client';

import { useAppStore } from '@/lib/store/use-app-store';
import { useMounted } from '@/lib/hooks/use-mounted';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useTheme } from 'next-themes';
import { useToast } from '@/hooks/use-toast';
import { Download, Upload, Trash2, Moon, Sun, CreditCard } from 'lucide-react';
import { Surface } from '@/components/primitives/surface/surface';
import { Panel, PanelHeader, PanelBody } from '@/components/primitives/panel/panel';
import { Stack } from '@/components/primitives/layout/stack';
import { useWorkspaceRegistration } from '@/lib/runtime';

export default function SettingsPage() {
  useWorkspaceRegistration({
    name: 'settings',
    label: 'Settings',
    icon: 'settings',
    deepLink: '/settings',
    defaultSurface: 'CONFIGURATION',
    supportedCommands: ['export', 'import', 'clear'],
    supportedFilters: [],
    supportedSelections: [],
  });

  const { theme, setTheme } = useTheme();
  const { cards, transactions, clearAllData } = useAppStore();
  const { toast } = useToast();
  const mounted = useMounted();
  const exportData = () => {
    const data = { cards, transactions, exportedAt: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `fintrack_backup_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'Export successful', description: 'Your data has been exported.' });
  };

  const importData = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (_e) => {
      try { toast({ title: 'Import successful', description: 'Your data has been imported.' }); }
      catch { toast({ title: 'Import failed', description: 'Invalid file format.', variant: 'destructive' }); }
    };
    reader.readAsText(file);
  };

  const handleClearData = () => {
    if (confirm('Are you sure? This will delete all your data permanently.')) {
      clearAllData();
      toast({ title: 'Data cleared', description: 'All your data has been removed.' });
    }
  };

  if (!mounted) return null;

  return (
    <Surface variant="default" density="none" className="flex flex-col h-full">
      <Panel fill>
        <PanelHeader title="Settings" />
        <PanelBody scrollable>
          <Stack gap={6} className="p-4">
            <Surface variant="raised" density="none" className="p-4">
              <Stack gap={4}>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  {theme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
                  Appearance
                </h2>
                <div className="flex items-center justify-between">
                  <div><p className="font-medium">Dark Mode</p><p className="text-sm text-[var(--text-tertiary)]">Toggle between light and dark theme</p></div>
                  <Switch checked={theme === 'dark'} onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')} />
                </div>
              </Stack>
            </Surface>
            <Surface variant="raised" density="none" className="p-4">
              <Stack gap={4}>
                <h2 className="text-lg font-semibold flex items-center gap-2"><CreditCard className="h-5 w-5" />Data Management</h2>
                <div className="flex items-center justify-between">
                  <div><p className="font-medium">Export Data</p><p className="text-sm text-[var(--text-tertiary)]">Download all your transactions and cards as JSON</p></div>
                  <Button variant="outline" onClick={exportData}><Download className="mr-2 h-4 w-4" />Export</Button>
                </div>
                <div className="flex items-center justify-between">
                  <div><p className="font-medium">Import Data</p><p className="text-sm text-[var(--text-tertiary)]">Restore from a previous backup</p></div>
                  <div className="relative">
                    <input type="file" accept=".json" onChange={importData} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                    <Button variant="outline"><Upload className="mr-2 h-4 w-4" />Import</Button>
                  </div>
                </div>
                <div className="flex items-center justify-between border-t pt-4">
                  <div>
                    <p className="font-medium text-[var(--color-negative-600)]">Clear All Data</p>
                    <p className="text-sm text-[var(--text-tertiary)]">Delete all transactions and cards permanently</p>
                  </div>
                  <Button variant="destructive" onClick={handleClearData}><Trash2 className="mr-2 h-4 w-4" />Clear All</Button>
                </div>
              </Stack>
            </Surface>
            <Surface variant="raised" density="none" className="p-4">
              <Stack gap={4}>
                <h2 className="text-lg font-semibold">About</h2>
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-full bg-[var(--surface-raised)] flex items-center justify-center text-3xl">💳</div>
                  <div><p className="font-bold text-lg">FinTrack</p><p className="text-sm text-[var(--text-tertiary)]">Bank Statement Parser Dashboard</p><p className="text-xs text-[var(--text-tertiary)] mt-1">Version 1.0.0</p></div>
                </div>
              </Stack>
            </Surface>
          </Stack>
        </PanelBody>
      </Panel>
    </Surface>
  );
}
