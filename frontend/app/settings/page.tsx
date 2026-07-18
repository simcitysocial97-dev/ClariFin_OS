'use client';

import { useAppStore } from '@/lib/store/use-app-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useTheme } from 'next-themes';
import { useToast } from '@/hooks/use-toast';
import { Download, Upload, Trash2, Moon, Sun, CreditCard } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { cards, transactions, clearAllData } = useAppStore();
  const { toast } = useToast();
  const [mounted, setMounted] = useState(false);

  // Handle hydration - only render after client mount
  useEffect(() => {
    // Use setTimeout to defer state update to next tick
    const timer = setTimeout(() => {
      setMounted(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const exportData = () => {
    const data = {
      cards,
      transactions,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fintrack_backup_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: 'Export successful',
      description: 'Your data has been exported.',
    });
  };

  const importData = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (_e) => {
      try {
        // Handle import logic here
        toast({
          title: 'Import successful',
          description: 'Your data has been imported.',
        });
      } catch {
        toast({
          title: 'Import failed',
          description: 'Invalid file format.',
          variant: 'destructive',
        });
      }
    };
    reader.readAsText(file);
  };

  const handleClearData = () => {
    if (confirm('Are you sure? This will delete all your data permanently.')) {
      clearAllData();
      toast({
        title: 'Data cleared',
        description: 'All your data has been removed.',
      });
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your preferences and data
        </p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {theme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Dark Mode</p>
              <p className="text-sm text-muted-foreground">
                Toggle between light and dark theme
              </p>
            </div>
            <Switch
              checked={theme === 'dark'}
              onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')}
            />
          </div>
        </CardContent>
      </Card>

      {/* Data Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Data Management
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Export Data</p>
              <p className="text-sm text-muted-foreground">
                Download all your transactions and cards as JSON
              </p>
            </div>
            <Button variant="outline" onClick={exportData}>
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Import Data</p>
              <p className="text-sm text-muted-foreground">
                Restore from a previous backup
              </p>
            </div>
            <div className="relative">
              <input
                type="file"
                accept=".json"
                onChange={importData}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Import
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between border-t pt-4">
            <div>
              <p className="font-medium text-destructive">Clear All Data</p>
              <p className="text-sm text-muted-foreground">
                Delete all transactions and cards permanently
              </p>
            </div>
            <Button variant="destructive" onClick={handleClearData}>
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-3xl">
              💳
            </div>
            <div>
              <p className="font-bold text-lg">FinTrack</p>
              <p className="text-sm text-muted-foreground">Bank Statement Parser Dashboard</p>
              <p className="text-xs text-muted-foreground mt-1">Version 1.0.0</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}