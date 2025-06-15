"""
UI Components for the accounting application.
This module contains reusable UI components and dialogs.
"""

# Import all components for easy access
from .dialogs import ModernAccountDialog, JournalEntryDialog
from .widgets import MetricCard, ActionCard, PageHeader, DateRangeSelector, SearchBar, ReportCard, SettingsCard
from .mica_effect import MicaEffect
from .styles import ModernStyles, GlassmorphismHelper
from .nl_report_dialog import NaturalLanguageReportDialog

__all__ = [
    'ModernAccountDialog',
    'JournalEntryDialog', 
    'MetricCard',
    'ActionCard',
    'PageHeader',
    'DateRangeSelector',
    'SearchBar',
    'ReportCard',
    'SettingsCard',
    'MicaEffect',
    'ModernStyles',
    'GlassmorphismHelper',
    'NaturalLanguageReportDialog'
]
