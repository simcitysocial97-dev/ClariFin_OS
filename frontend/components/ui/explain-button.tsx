'use client';

import { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface ExplainButtonProps {
  title: string;
  explanation: string;
}

export function ExplainButton({ title, explanation }: ExplainButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon-xs"
          className="h-5 w-5 rounded-full p-0 hover:bg-muted"
          aria-label={`Explain ${title}`}
        >
          <HelpCircle className="h-3 w-3 text-muted-foreground" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-sm">{title}</DialogTitle>
          <DialogDescription className="text-xs leading-relaxed">
            {explanation}
          </DialogDescription>
        </DialogHeader>
      </DialogContent>
    </Dialog>
  );
}