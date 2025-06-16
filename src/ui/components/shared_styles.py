"""
Shared styling functions for journal and bulk entry components.
Consolidates all the duplicate styling code into one place.
"""

def get_field_style(field_type="default"):
    """Get styling for input fields based on type."""
    base_style = """
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 6px;
        padding: 4px 8px;
        font-weight: 500;
        font-size: 13px;
        min-height: 20px;
        max-height: 32px;
        line-height: 20px;
    """
    
    # Additional styling for editable combo boxes
    combo_style = """
        QLineEdit {
            background: transparent;
            border: none;
            padding: 0px 0px;
            font-weight: 500;
            font-size: 13px;
            min-height: 20px;
            max-height: 32px;
            line-height: 20px;
        }
        QLineEdit::placeholder {
            color: rgba(255, 255, 255, 0.5);
            font-style: italic;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            margin-top: 2px;
            margin-bottom: 2px;
            margin-right: 2px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid rgba(255, 255, 255, 0.7);
            width: 0px;
            height: 0px;
        }
        QComboBox:focus {
            border-color: rgba(0, 120, 215, 0.8);
            background: rgba(255, 255, 255, 0.12);
        }
        QComboBox QAbstractItemView {
            background: rgba(40, 40, 40, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            selection-background-color: rgba(0, 120, 215, 0.6);
            color: white;
            padding: 4px;
            font-size: 13px;
        }
        QComboBox QAbstractItemView::item {
            padding: 8px;
            border-radius: 4px;
            margin: 1px;
            min-height: 20px;
        }
        QComboBox QAbstractItemView::item:hover {
            background: rgba(255, 255, 255, 0.1);
        }
    """
    
    if field_type == "date":
        return base_style + """
            color: rgba(255, 255, 255, 0.9);
            QDateEdit::up-button, QDateEdit::down-button {
                width: 16px;
                height: 16px;
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }
            QDateEdit::up-arrow, QDateEdit::down-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
            }
            QDateEdit::up-arrow {
                border-bottom: 5px solid rgba(255, 255, 255, 0.7);
            }
            QDateEdit::down-arrow {
                border-top: 5px solid rgba(255, 255, 255, 0.7);
            }
        """
    elif field_type == "description":
        return base_style + """
            color: rgba(255, 255, 255, 0.9);
        """
    elif field_type == "debit":
        return base_style + combo_style + """
            color: rgba(255, 100, 100, 0.9);
        """
    elif field_type == "credit":
        return base_style + combo_style + """
            color: rgba(100, 255, 100, 0.9);
        """
    elif field_type == "amount":
        return base_style + """
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            text-align: right;
        """
    else:
        return base_style + """
            color: rgba(255, 255, 255, 0.9);
        """


def get_button_style(primary=False, secondary=False):
    """Get styling for buttons."""
    if primary:
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(34, 139, 34, 0.8), stop:1 rgba(0, 100, 0, 0.8));
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                min-width: 60px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(34, 139, 34, 1.0), stop:1 rgba(0, 100, 0, 1.0));
            }
        """
    elif secondary:
        return """
            QPushButton {
                background: rgba(255, 100, 100, 0.3);
                border: 1px solid rgba(255, 100, 100, 0.5);
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.5);
                border-color: rgba(255, 100, 100, 0.8);
            }
        """
    else:
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
            }
        """


def load_accounts_from_system(system):
    """Shared function to load accounts from the accounting system."""
    try:
        if hasattr(system, 'get_all_accounts'):
            accounts_data = system.get_all_accounts()
            return [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]  # Only postable accounts
        else:
            return [
                "1001 - Cash",
                "1002 - Bank Account", 
                "1100 - Accounts Receivable",
                "2001 - Accounts Payable",
                "3001 - Owner's Equity",
                "4001 - Sales Revenue",
                "5001 - Cost of Goods Sold",
                "6001 - Operating Expenses"
            ]
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return ["1001 - Cash", "1002 - Bank Account"]  # Minimal fallback


def populate_account_combo(combo, accounts):
    """Shared function to populate account combo boxes."""
    try:
        combo.setAccountList(accounts)
        combo.setPlaceholderText("Select or type account...")
        combo.clear_selection()
    except Exception as e:
        print(f"Error populating account combo: {e}")
        combo.clear()
        for account in accounts:
            combo.addItem(account)
