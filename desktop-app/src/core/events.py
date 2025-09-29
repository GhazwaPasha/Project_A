from PyQt6.QtCore import QObject, pyqtSignal

class AccountingSystemEvents(QObject):
    """Event system for accounting system changes."""
    accounts_changed = pyqtSignal()  # Emitted when accounts are added, edited, or deleted
    entry_added = pyqtSignal()       # Emitted when a journal entry is added
    
# Global event emitter
accounting_events = AccountingSystemEvents()