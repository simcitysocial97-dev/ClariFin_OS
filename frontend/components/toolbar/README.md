# Workspace Toolbar - Stage 3 Transaction Intelligence Workspace

## Overview

The Workspace Toolbar provides action buttons and status indicators for the Transaction Intelligence Workspace.

## Components

### WorkspaceToolbar

A responsive toolbar with action buttons and transaction count display.

```tsx
import { WorkspaceToolbar } from '@/components/toolbar';

<WorkspaceToolbar
  onSearchClick={() => {}}
  onFilterToggle={() => {}}
  onGroupToggle={() => {}}
  onSortToggle={() => {}}
  onExport={() => {}}
  onRefresh={() => {}}
  onSettings={() => {}}
  transactionCount={100}
  activeFilterCount={3}
  loading={false}
/>
```

**Props:**
- `onSearchClick`: Callback for search button click
- `onFilterToggle`: Callback for filter toggle
- `onGroupToggle`: Callback for group toggle
- `onSortToggle`: Callback for sort toggle
- `onExport`: Callback for export button click
- `onRefresh`: Callback for refresh button click
- `onSettings`: Callback for settings button click
- `transactionCount`: Number of transactions to display
- `activeFilterCount`: Number of active filters (shows badge when > 0)
- `loading`: Optional loading state for refresh button (default: false)
- `error`: Optional error message to display
- `onErrorRetry`: Optional callback for error retry
- `showSearch`: Show/hide search button (default: true)
- `showFilter`: Show/hide filter button (default: true)
- `showGroup`: Show/hide group button (default: true)
- `showSort`: Show/hide sort button (default: true)
- `showExport`: Show/hide export button (default: true)
- `showRefresh`: Show/hide refresh button (default: true)
- `showSettings`: Show/hide settings button (default: true)

## Features

### Action Buttons

- **Search**: Opens search dialog (Ctrl+F)
- **Filter**: Opens filter panel (Ctrl+Shift+F) - shows badge with count when filters active
- **Group**: Toggles grouping (Ctrl+G)
- **Sort**: Opens sort options (Ctrl+S)
- **Export**: Exports transactions to CSV
- **Refresh**: Refreshes data (Ctrl+R) - shows loading spinner when active
- **Settings**: Opens settings panel

### Responsive Design

- Stacks vertically on mobile
- Horizontal layout on desktop (sm breakpoint)
- Button labels visible on mobile, icons only on desktop

### Dark Mode

Uses `bg-background` classes for proper dark mode support.

### Accessibility

- `role="toolbar"` for semantic structure
- `aria-label` on all buttons with keyboard shortcut hints
- Filter count badge has `aria-hidden="true"` to avoid redundancy

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd + F | Search |
| Ctrl/Cmd + Shift + F | Filter |
| Ctrl/Cmd + G | Group |
| Ctrl/Cmd + S | Sort |
| Ctrl/Cmd + R | Refresh |

## Performance

All render operations complete under 100ms for optimal user experience.