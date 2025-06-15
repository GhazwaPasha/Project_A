# NonScrollableComboBox Implementation

## Problem Solved
The original QComboBox widgets in the journal entry and bulk entry forms were susceptible to accidental changes when users scrolled with their mouse wheel while the cursor was over the combo box fields. This could lead to unintended account selections, especially problematic in accounting applications where accuracy is critical.

## Solution
Implemented a custom `NonScrollableComboBox` class that extends QComboBox and overrides the `wheelEvent` method to ignore wheel events unless the combo box:
1. Has keyboard focus AND
2. Has its dropdown list open

## Implementation Details

### Files Modified:
- `src/ui/components/widgets.py` - Added NonScrollableComboBox class
- `src/ui/pages/journal.py` - Updated debit/credit account fields to use NonScrollableComboBox
- `src/ui/pages/bulk_entry.py` - Updated all account selection combo boxes to use NonScrollableComboBox

### Behavior:
- **Normal scrolling over the combo box**: Ignored (no change in selection)
- **Focused combo box with closed dropdown**: Ignored (no change in selection)
- **Focused combo box with open dropdown**: Normal wheel scrolling works (for navigation within dropdown)

### Benefits:
1. Prevents accidental account changes while scrolling through forms
2. Maintains full functionality when user intentionally wants to scroll through options
3. Provides better user experience and data accuracy
4. Zero impact on existing functionality when used intentionally

## Usage
The NonScrollableComboBox can be used as a drop-in replacement for QComboBox anywhere scroll prevention is desired:

```python
from src.ui.components.widgets import NonScrollableComboBox

# Replace QComboBox with NonScrollableComboBox
account_combo = NonScrollableComboBox()
account_combo.addItems(["Account 1", "Account 2", "Account 3"])
```

## Testing
The implementation has been tested in both the journal entry form and bulk entry table to ensure:
- Accidental scrolling is prevented
- Intentional navigation still works when dropdown is open
- No impact on other combo box functionality (styling, data binding, etc.)
