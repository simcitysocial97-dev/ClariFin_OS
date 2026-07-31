# Workspace Layout Documentation

## Overview

The Transaction Intelligence Workspace is the canonical workspace for exploring, understanding, verifying, and acting upon financial transactions.

## Layout Structure

```
+------------------------------------------------------+
| Toolbar                                              |
+------------------------------------------------------+
| Filter Panel                                         |
+------------------------------------------------------+
| Transaction Grid / Table                             |
+------------------------------------------------------+
| Selection Summary                                    |
+------------------------------------------------------+
| Insight Panel                                        |
+------------------------------------------------------+
| Evidence Drawer                                      |
+------------------------------------------------------+
| Action Drawer                                        |
+------------------------------------------------------+
```

## Regions

### Toolbar
- Search button
- Filter toggle
- Group toggle
- Sort toggle
- Export button
- Refresh button
- Settings button
- Transaction count
- Active filter count

### Filter Panel
- Date filter
- Category filter
- Merchant filter
- Amount filter
- Status filter

### Transaction Table
- Table header
- Table rows
- Table cells
- Pagination controls
- Virtualization support

### Selection Summary
- Selected count
- Total count
- Clear selection button
- Select all button

### Insight Panel
- Transaction insights
- Group summaries
- Statistics

### Evidence Drawer
- Evidence summary
- Evidence list
- Evidence item
- Source link
- Calculation view

### Action Drawer
- Bulk action controls
- Categorize action
- Adjust action
- Delete action

## Keyboard Shortcuts

- Ctrl/Cmd + F: Focus search
- Ctrl/Cmd + Shift + F: Toggle filter panel
- Ctrl/Cmd + G: Toggle group
- Ctrl/Cmd + S: Toggle sort
- Ctrl/Cmd + R: Refresh
- Ctrl/Cmd + A: Select all visible
- Delete: Clear selection
- Escape: Close evidence drawer

## Responsive Design

- Mobile: Stacked layout with collapsible panels
- Tablet: Two-column layout
- Desktop: Full layout with all regions visible

## Dark Mode

All components support dark mode with proper theme classes:
- `bg-background dark:bg-background`
- `text-foreground dark:text-foreground`
- Proper color contrast for all states