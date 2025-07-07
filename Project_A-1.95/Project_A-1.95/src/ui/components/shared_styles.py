"""
Shared styling functions for the accounting application.
"""

def get_field_style(field_type="default"):
    """Get consistent styling for form fields across the application."""
    base_style = """
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 5px;
        padding: 6px 8px;
        color: rgba(255, 255, 255, 0.95);
        font-size: 12px;
        font-weight: 400;
        selection-background-color: rgba(100, 150, 255, 0.3);
        min-height: 26px;
        max-height: 26px;
    """
    
    # Field-specific width and styling adjustments
    if field_type == "date":
        return base_style + """
            max-width: 120px;
            min-width: 120px;
        """
    elif field_type == "description":
        return base_style + """
            max-width: 200px;
            min-width: 180px;
        """
    elif field_type in ["debit", "credit"]:
        return base_style + """
            max-width: 200px;
            min-width: 160px;
        """
    elif field_type == "amount":
        return base_style + """
            max-width: 120px;
            min-width: 100px;
        """
    
    return base_style

def get_button_style(primary=False, secondary=False, compact=False):
    """Get consistent styling for buttons across the application."""
    # Base padding and height for regular buttons
    padding = "8px 16px"
    min_height = "26px"
    
    # Compact styling for smaller buttons
    if compact:
        padding = "6px 12px"
        min_height = "22px"
    
    base_style = f"""
        QPushButton {{
            background: rgba(100, 181, 246, 0.2);
            border: 1px solid rgba(100, 181, 246, 0.4);
            border-radius: 6px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 11px;
            padding: {padding};
            min-height: {min_height};
            max-width: 80px;
        }}
        QPushButton:hover {{
            background: rgba(100, 181, 246, 0.3);
            border-color: rgba(100, 181, 246, 0.6);
        }}
        QPushButton:pressed {{
            background: rgba(100, 181, 246, 0.4);
        }}
    """
    
    if primary:
        return f"""
            QPushButton {{
                background: rgba(100, 181, 246, 0.4);
                border: 1px solid rgba(100, 181, 246, 0.6);
                border-radius: 6px;
                color: white;
                font-weight: 600;
                font-size: 11px;
                padding: {padding};
                min-height: {min_height};
                max-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(100, 181, 246, 0.5);
                border-color: rgba(100, 181, 246, 0.8);
            }}
            QPushButton:pressed {{
                background: rgba(100, 181, 246, 0.6);
            }}
        """
    elif secondary:
        return f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-weight: 600;
                font-size: 11px;
                padding: {padding};
                min-height: {min_height};
                max-width: 80px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """
    
    return base_style

def get_label_style(field_type=None):
    """Get consistent styling for field labels across the application."""
    return """
        color: rgba(255, 255, 255, 0.8);
        font-size: 9px;
        font-weight: 700;
        background: transparent;
        border: none;
        padding: 1px 2px;
        margin: 0px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        min-height: 14px;
        max-height: 14px;
    """

def load_accounts_from_system(system):
    """Load accounts from the accounting system."""
    try:
        if hasattr(system, 'get_chart_of_accounts'):
            accounts_data = system.get_chart_of_accounts(active_only=False)
            # Handle both dict and tuple formats
            if accounts_data and len(accounts_data) > 0:
                sample_account = accounts_data[0]
                if isinstance(sample_account, tuple):
                    # Tuple format: (name, type, code, parent_code, level, is_postable, description)
                    return [f"{acc[2]} - {acc[0]}" for acc in accounts_data if len(acc) > 5 and acc[5]]
                else:
                    # Dict format
                    return [f"{acc['code']} - {acc['name']}" for acc in accounts_data if acc.get('is_postable', True)]
        elif hasattr(system, 'get_postable_accounts'):
            # Use the specific method for postable accounts
            accounts_data = system.get_postable_accounts()
            if accounts_data and len(accounts_data) > 0:
                sample_account = accounts_data[0]
                if isinstance(sample_account, tuple):
                    # Tuple format: (name, type, code, parent_code, level, is_postable, description)
                    return [f"{acc[2]} - {acc[0]}" for acc in accounts_data if len(acc) >= 3]
                else:
                    # Dict format
                    return [f"{acc['code']} - {acc['name']}" for acc in accounts_data]
        elif hasattr(system, 'get_all_accounts'):
            accounts_data = system.get_all_accounts()
            # Handle tuple format: (name, type, code, parent_code, level, is_postable, description)
            if accounts_data and len(accounts_data) > 0:
                sample_account = accounts_data[0]
                if isinstance(sample_account, tuple):
                    return [f"{acc[2]} - {acc[0]}" for acc in accounts_data if len(acc) > 5 and acc[5]]  # acc[5] is is_postable
                else:
                    return [f"{acc['code']} - {acc['name']}" for acc in accounts_data if acc.get('is_postable', True)]
        else:
            return ["1001 - Cash", "2001 - Accounts Payable"]
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return ["1001 - Cash", "2001 - Accounts Payable"]

def populate_account_combo(combo, accounts):
    """Populate an account combo box with accounts."""
    try:
        combo.setAccountList(accounts)
        combo.setPlaceholderText("Select or type account...")
        combo.clear_selection()
    except Exception as e:
        print(f"Error populating combo: {e}")
