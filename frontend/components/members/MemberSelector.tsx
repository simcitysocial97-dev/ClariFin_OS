'use client';

import { useState } from 'react';
import { useMember } from '@/lib/context/member-context';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { Plus, User } from 'lucide-react';
import { cn } from '@/lib/utils';

const PRESET_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#3b82f6', // blue
  '#8b5cf6', // purple
];

interface MemberSelectorProps {
  showLabel?: boolean;
  className?: string;
}

export function MemberSelector({ showLabel = true, className }: MemberSelectorProps) {
  const { member, setMember, members, addMember } = useMember();
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newMemberName, setNewMemberName] = useState('');
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[0]);
  const [adding, setAdding] = useState(false);

  const handleAddMember = async () => {
    if (!newMemberName.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter a name for the new member.',
        variant: 'destructive',
      });
      return;
    }

    setAdding(true);
    try {
      if (!newMemberName.trim() || !selectedColor) return;
      await addMember(newMemberName.trim(), selectedColor);
      toast({
        title: 'Member added',
        description: `${newMemberName} has been added successfully.`,
      });
      setNewMemberName('');
      setSelectedColor(PRESET_COLORS[0]);
      setDialogOpen(false);
    } catch (error) {
      toast({
        title: 'Failed to add member',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className={cn('space-y-2', className)}>
      {showLabel && (
        <label className="text-sm font-medium text-muted-foreground">Viewing as</label>
      )}
      <Select value={member || "All"} onValueChange={setMember}>
        <SelectTrigger>
          <SelectValue placeholder="Select member" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="All">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4" />
              All Members
            </div>
          </SelectItem>
          {members.map((m) => (
            <SelectItem key={m.id} value={m.name}>
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: m.color }}
                />
                {m.name}
              </div>
            </SelectItem>
          ))}
          <div className="border-t mt-1 pt-1">
            <button
              className="flex w-full items-center gap-2 px-2 py-1.5 text-sm text-muted-foreground hover:text-foreground cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4" />
              Add Member
            </button>
          </div>
        </SelectContent>
      </Select>

      {/* Add Member Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Member</DialogTitle>
            <DialogDescription>
              Add a family member to track their transactions separately.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input
                placeholder="Enter member name"
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Color</label>
              <div className="flex gap-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className={cn(
                      'h-8 w-8 rounded-full border-2 transition-all',
                      selectedColor === color
                        ? 'border-foreground scale-110'
                        : 'border-transparent'
                    )}
                    style={{ backgroundColor: color }}
                    onClick={() => setSelectedColor(color)}
                  />
                ))}
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddMember} disabled={adding}>
              {adding ? 'Adding...' : 'Add Member'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}