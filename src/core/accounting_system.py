import sqlite3
import uuid
from datetime import datetime, timedelta
import random

class AccountingSystem:
    def __init__(self, db_path='accounting.db'):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                debit_account TEXT,
                credit_account TEXT,
                amount REAL,
                timestamp TEXT
            )
        ''')
        
        # Check if accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        accounts_exists = cursor.fetchone() is not None
        
        if not accounts_exists:
            # Create new accounts table with enhanced hierarchy columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    name TEXT PRIMARY KEY,
                    type TEXT,
                    code TEXT,
                    parent_code TEXT,
                    level INTEGER DEFAULT 1,
                    is_postable BOOLEAN DEFAULT 1,
                    description TEXT
                )
            ''')
        else:
            # Check if new columns exist and add them if needed
            cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'code' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN code TEXT')
                
            if 'parent_code' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN parent_code TEXT')
                
            if 'level' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN level INTEGER DEFAULT 1')
                
            if 'is_postable' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN is_postable BOOLEAN DEFAULT 1')
                
            if 'description' not in columns:
                cursor.execute('ALTER TABLE accounts ADD COLUMN description TEXT')
        
        self.conn.commit()
        # Insert hierarchical accounts if table is empty
        cursor.execute('SELECT COUNT(*) FROM accounts')
        if cursor.fetchone()[0] == 0:
            # Use hierarchical structure instead of flat mock accounts
            self.seed_hierarchical_accounts()
        # Update existing accounts with codes if needed
        else:
            # Check if we need to reseed with proper hierarchy
            cursor.execute('SELECT COUNT(*) FROM accounts WHERE level > 1')
            hierarchical_count = cursor.fetchone()[0]
            
            if hierarchical_count == 0:
                # We have old flat structure, reseed with hierarchy
                cursor.execute('DELETE FROM accounts')
                self.seed_hierarchical_accounts()
            else:
                # Update existing accounts with codes if needed
                self._update_existing_accounts_data()
            
            self.conn.commit()
            
    def add_journal_entry(self, date, description, debit_account, credit_account, amount):
        # Helper to get or add account type and generate code
        def get_or_add_account_type(account):
            if not account:
                # If account is blank, do not prompt, just return None (for GUI safety)
                return None
                
            cursor = self.conn.cursor()
            # Check if input is an account code
            if len(account) == 4 and account.isdigit():
                cursor.execute('SELECT type FROM accounts WHERE code = ?', (account,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                    
            # Otherwise, look up by name
            cursor.execute('SELECT type, code FROM accounts WHERE name = ?', (account,))
            row = cursor.fetchone()
            if row:
                return row[0]
                
            # If account not found, return None (account must exist in chart of accounts)
            return None
            
        debit_type = get_or_add_account_type(debit_account)
        credit_type = get_or_add_account_type(credit_account)
        
        # Enforce double-entry: one debit, one credit, same amount
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        # Get the actual account names if codes were provided
        def resolve_account(account):
            if len(account) == 4 and account.isdigit():
                cursor.execute('SELECT name FROM accounts WHERE code = ?', (account,))
                row = cursor.fetchone()
                if row:
                    return row[0]
            return account
            
        debit_name = resolve_account(debit_account)
        credit_name = resolve_account(credit_account)
        
        cursor.execute('''
            INSERT INTO journal_entries (id, date, description, debit_account, credit_account, amount, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (entry_id, date, description, debit_name, credit_name, amount, timestamp))
        self.conn.commit()
        return entry_id

    def get_ledger(self, account_name, from_date=None, to_date=None):
        cursor = self.conn.cursor()
        if from_date and to_date:
            cursor.execute('''
                SELECT date, description, debit_account, credit_account, amount FROM journal_entries
                WHERE (debit_account = ? OR credit_account = ?) AND date BETWEEN ? AND ?
                ORDER BY date
            ''', (account_name, account_name, from_date, to_date))
        else:
            cursor.execute('''
                SELECT date, description, debit_account, credit_account, amount FROM journal_entries
                WHERE debit_account = ? OR credit_account = ?
                ORDER BY date
            ''', (account_name, account_name))
        return cursor.fetchall()

    def get_trial_balance(self, from_date=None, to_date=None):
        cursor = self.conn.cursor()
        if from_date and to_date:
            cursor.execute('''
                SELECT debit_account AS account, SUM(amount) AS debit, 0 AS credit FROM journal_entries WHERE date BETWEEN ? AND ? GROUP BY debit_account
                UNION ALL
                SELECT credit_account AS account, 0 AS debit, SUM(amount) AS credit FROM journal_entries WHERE date BETWEEN ? AND ? GROUP BY credit_account
            ''', (from_date, to_date, from_date, to_date))
        else:
            cursor.execute('''
                SELECT debit_account AS account, SUM(amount) AS debit, 0 AS credit FROM journal_entries GROUP BY debit_account
                UNION ALL
                SELECT credit_account AS account, 0 AS debit, SUM(amount) AS credit FROM journal_entries GROUP BY credit_account
            ''')
        rows = cursor.fetchall()
        balance = {}
        for account, debit, credit in rows:
            if account not in balance:
                balance[account] = 0
            balance[account] += (debit - credit)
        return balance

    # Placeholder for report generation methods
    def generate_income_statement(self, period_start=None, period_end=None):
        cursor = self.conn.cursor()
        # Default: all time
        query = '''SELECT debit_account, credit_account, amount, date FROM journal_entries'''
        params = ()
        if period_start and period_end:
            query += ' WHERE date BETWEEN ? AND ?'
            params = (period_start, period_end)
        cursor.execute(query, params)
        revenue = 0
        expenses = 0
        for debit, credit, amount, date in cursor.fetchall():
            # Defensive: handle None values
            debit = debit or ''
            credit = credit or ''
            # Simple logic: if account contains 'Revenue' or 'Sales', treat as revenue; if 'Expense', treat as expense
            if 'Revenue' in credit or 'Sales' in credit:
                revenue += amount
            if 'Expense' in debit or 'Cost' in debit:
                expenses += amount
        net_income = revenue - expenses
        return {'revenue': revenue, 'expenses': expenses, 'net_income': net_income}

    def generate_income_statement_breakdown(self, from_date=None, to_date=None):
        cursor = self.conn.cursor()
        query = '''SELECT debit_account, credit_account, amount, date FROM journal_entries'''
        params = ()
        if from_date and to_date:
            query += ' WHERE date BETWEEN ? AND ?'
            params = (from_date, to_date)
        cursor.execute(query, params)
        revenues = {}
        expenses = {}
        cogs = {}
        for debit, credit, amount, date in cursor.fetchall():
            # Revenue
            if credit and ("Revenue" in credit or "Sales" in credit or "Income" in credit):
                revenues[credit] = revenues.get(credit, 0) + amount
            # COGS
            if debit and ("Cost of Goods Sold" in debit or "COGS" in debit):
                cogs[debit] = cogs.get(debit, 0) + amount
            # Expenses
            if debit and ("Expense" in debit or "Rent" in debit or "Salary" in debit or "Utilities" in debit or "Wages" in debit or "Advertising" in debit or "Insurance" in debit or "Depreciation" in debit):
                expenses[debit] = expenses.get(debit, 0) + amount
        total_revenue = sum(revenues.values())
        total_cogs = sum(cogs.values())
        gross_profit = total_revenue - total_cogs
        total_expenses = sum(expenses.values())
        net_income = gross_profit - total_expenses
        return {
            'revenues': sorted(revenues.items()),
            'total_revenue': total_revenue,
            'cogs': sorted(cogs.items()),
            'total_cogs': total_cogs,
            'gross_profit': gross_profit,
            'expenses': sorted(expenses.items()),
            'total_expenses': total_expenses,
            'net_income': net_income
        }

    def generate_balance_sheet(self, as_of_date=None):
        cursor = self.conn.cursor()
        # Default: all time
        query = '''SELECT debit_account, credit_account, amount, date FROM journal_entries'''
        params = ()
        if as_of_date:
            query += ' WHERE date <= ?'
            params = (as_of_date,)
        cursor.execute(query, params)
        accounts = {}
        for debit, credit, amount, date in cursor.fetchall():
            accounts[debit] = accounts.get(debit, 0) + amount
            accounts[credit] = accounts.get(credit, 0) - amount
        # Group by type if available (not implemented here)
        return accounts

    def generate_balance_sheet_breakdown(self, as_of_date=None):
        cursor = self.conn.cursor()
        query = '''SELECT debit_account, credit_account, amount, date FROM journal_entries'''
        params = ()
        if as_of_date:
            query += ' WHERE date <= ?'
            params = (as_of_date,)
        cursor.execute(query, params)
        accounts = {}
        for debit, credit, amount, date in cursor.fetchall():
            accounts[debit] = accounts.get(debit, 0) + amount
            accounts[credit] = accounts.get(credit, 0) - amount        # Group by type
        assets, liabilities, equity = [], [], []
        total_assets = total_liabilities = total_equity = 0.0
        for name, acc_type, code, parent_code, level, is_postable, description in self.get_all_accounts():
            bal = accounts.get(name, 0.0)
            if acc_type == 'Asset':
                assets.append((name, bal))
                total_assets += bal
            elif acc_type == 'Liability':
                liabilities.append((name, bal))
                total_liabilities += bal
            elif acc_type == 'Equity':
                equity.append((name, bal))
                total_equity += bal
        check = f"{total_assets:,.2f} = {total_liabilities + total_equity:,.2f}"
        return {
            'assets': assets,
            'total_assets': total_assets,
            'liabilities': liabilities,
            'total_liabilities': total_liabilities,
            'equity': equity,
            'total_equity': total_equity,
            'check': check
        }

    def generate_cash_flow_statement(self, period_start=None, period_end=None):
        cursor = self.conn.cursor()
        query = '''SELECT debit_account, credit_account, amount, date FROM journal_entries'''
        params = ()
        if period_start and period_end:
            query += ' WHERE date BETWEEN ? AND ?'
            params = (period_start, period_end)
        cursor.execute(query, params)
        cash_in = 0
        cash_out = 0
        for debit, credit, amount, date in cursor.fetchall():
            if debit == 'Cash':
                cash_in += amount
            if credit == 'Cash':
                cash_out += amount
        net_cash = cash_in - cash_out
        return {'cash_in': cash_in, 'cash_out': cash_out, 'net_cash': net_cash}

    def generate_cash_flow_breakdown(self, from_date=None, to_date=None):
        cursor = self.conn.cursor()
        query = '''SELECT debit_account, credit_account, amount, date, description FROM journal_entries'''
        params = ()
        if from_date and to_date:
            query += ' WHERE date BETWEEN ? AND ?'
            params = (from_date, to_date)
        cursor.execute(query, params)
        # Simple direct method: classify by keywords
        operating, investing, financing = [], [], []
        net_operating = net_investing = net_financing = 0.0
        for debit, credit, amount, date, desc in cursor.fetchall():
            desc = desc.lower() if desc else ''
            # Operating: most cash receipts/payments, expenses, sales
            if any(word in desc for word in ['sale', 'revenue', 'customer', 'rent', 'salary', 'utilities', 'wages', 'advertising', 'insurance', 'expense']):
                operating.append((desc, amount))
                net_operating += amount if debit == 'Cash' else -amount if credit == 'Cash' else 0
            # Investing: equipment, inventory, asset purchases
            elif any(word in desc for word in ['equipment', 'inventory', 'asset', 'purchase']):
                investing.append((desc, amount))
                net_investing += amount if debit == 'Cash' else -amount if credit == 'Cash' else 0
            # Financing: loans, capital, equity, owner
            elif any(word in desc for word in ['loan', 'capital', 'equity', 'owner']):
                financing.append((desc, amount))
                net_financing += amount if debit == 'Cash' else -amount if credit == 'Cash' else 0
        net_cash_flow = net_operating + net_investing + net_financing
        return {
            'operating activities': operating,
            'net_operating activities': net_operating,
            'investing activities': investing,
            'net_investing activities': net_investing,
            'financing activities': financing,
            'net_financing activities': net_financing,
            'net_cash_flow': net_cash_flow,
            'operating activities': operating,
            'investing activities': investing,
            'financing activities': financing,
            'net_operating': net_operating,
            'net_investing': net_investing,
            'net_financing': net_financing
        }

    def generate_account_code(self, acc_type):
        """
        Generate a sequential 4-digit code based on account type.
        First digit is based on type: 1-Asset, 2-Liability, 3-Equity, 4-Revenue, 5-Expense
        Remaining digits are sequential within that type.
        """
        prefix_map = {
            'Asset': '1',
            'Liability': '2',
            'Equity': '3', 
            'Revenue': '4',
            'Expense': '5'
        }
        
        prefix = prefix_map.get(acc_type, '9')  # Default to 9 for unknown types
        
        # Find the highest existing code for this type
        cursor = self.conn.cursor()
        cursor.execute('SELECT code FROM accounts WHERE type = ? AND code LIKE ?', 
                      (acc_type, f'{prefix}%'))
        
        codes = [row[0] for row in cursor.fetchall() if row[0] is not None]
        
        if not codes:
            # First account of this type
            return f"{prefix}000"
            
        # Find the highest code and increment
        highest_code = max(codes)
        if highest_code and len(highest_code) >= 4:
            try:
                next_num = int(highest_code) + 1
                return f"{next_num:04d}"
            except ValueError:
                # If there's an error converting to int, start with basic code
                return f"{prefix}000"
        else:
            return f"{prefix}000"

    def get_all_accounts(self):
        """Get all accounts ordered by code for proper hierarchy display."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, parent_code, level, is_postable, description FROM accounts ORDER BY code')
        return cursor.fetchall()
    
    def get_account_hierarchy(self):
        """Get accounts in a hierarchical structure."""
        all_accounts = self.get_all_accounts()
        # Create a dictionary of accounts by code
        accounts_by_code = {code: {'name': name, 'type': acc_type, 'code': code, 
                                 'parent_code': parent_code, 'level': level, 
                                 'is_postable': is_postable, 'description': description, 'children': []} 
                          for name, acc_type, code, parent_code, level, is_postable, description in all_accounts}
        
        # Build hierarchy
        root_accounts = []
        for code, account in accounts_by_code.items():
            parent_code = account['parent_code']
            if parent_code and parent_code in accounts_by_code:
                accounts_by_code[parent_code]['children'].append(account)
            else:
                root_accounts.append(account)
                
        return root_accounts
        
    def get_account_by_code(self, code):
        """Get account details by account code."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, parent_code, level, is_postable, description FROM accounts WHERE code = ?', (code,))
        result = cursor.fetchone()
        return result if result else (None, None, None, None, None, None)

    def add_account(self, name, acc_type, code=None, parent_code=None, level=1, is_postable=True, description=""):
        """Add a new account with hierarchy support."""
        cursor = self.conn.cursor()
        
        if not code:
            code = self.generate_account_code(acc_type)
            
        cursor.execute('INSERT INTO accounts (name, type, code, parent_code, level, is_postable, description) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                      (name, acc_type, code, parent_code, level, is_postable, description))
        self.conn.commit()
        return code

    def edit_account(self, old_name, new_name, new_type, new_code=None, new_parent_code=None, new_level=None, new_is_postable=None, new_description=None):
        """Update an existing account with enhanced hierarchy support."""
        cursor = self.conn.cursor()
        
        # Get current account details
        cursor.execute('SELECT type, code, parent_code, level, is_postable, description FROM accounts WHERE name = ?', (old_name,))
        current = cursor.fetchone()
        if not current:
            return
            
        old_type, old_code, old_parent, old_level, old_is_postable, old_description = current
        
        # If code is not provided, keep the existing one or generate new if type changed
        if new_code is None:
            if old_type != new_type:
                new_code = self.generate_account_code(new_type)
            else:
                new_code = old_code
                
        # Keep existing values if new ones not provided
        if new_parent_code is None:
            new_parent_code = old_parent
        if new_level is None:
            new_level = old_level
        if new_is_postable is None:
            new_is_postable = old_is_postable
        if new_description is None:
            new_description = old_description
                
        cursor.execute('UPDATE accounts SET name = ?, type = ?, code = ?, parent_code = ?, level = ?, is_postable = ?, description = ? WHERE name = ?', 
                      (new_name, new_type, new_code, new_parent_code, new_level, new_is_postable, new_description, old_name))
        self.conn.commit()

    def delete_account(self, name):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE name = ?', (name,))
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_recent_journal_entries(self, limit=20):
        """Get recent journal entries ordered by date descending."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, date, description, debit_account, credit_account, amount, timestamp FROM journal_entries ORDER BY date DESC, timestamp DESC LIMIT ?", (limit,))
        
        entries = []
        for row in cursor.fetchall():
            entries.append({
                'id': row[0],
                'date': row[1],
                'description': row[2],
                'debit_account': row[3],
                'credit_account': row[4],
                'amount': row[5],
                'timestamp': row[6]
            })
        return entries

    def get_journal_entries(self, from_date=None, to_date=None):
        """Get journal entries filtered by date range."""
        cursor = self.conn.cursor()
        
        if from_date and to_date:
            cursor.execute("""
                SELECT id, date, description, debit_account, credit_account, amount, timestamp 
                FROM journal_entries 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date DESC, timestamp DESC
            """, (from_date, to_date))
        elif from_date:
            cursor.execute("""
                SELECT id, date, description, debit_account, credit_account, amount, timestamp 
                FROM journal_entries 
                WHERE date >= ? 
                ORDER BY date DESC, timestamp DESC
            """, (from_date,))
        elif to_date:
            cursor.execute("""
                SELECT id, date, description, debit_account, credit_account, amount, timestamp 
                FROM journal_entries 
                WHERE date <= ? 
                ORDER BY date DESC, timestamp DESC
            """, (to_date,))
        else:
            cursor.execute("""
                SELECT id, date, description, debit_account, credit_account, amount, timestamp 
                FROM journal_entries 
                ORDER BY date DESC, timestamp DESC
            """)
        
        return cursor.fetchall()

    def get_journal_entries_by_date_range(self, from_date, to_date):
        """Wrapper for get_journal_entries to support the journal UI's expected method name."""
        return self.get_journal_entries(from_date, to_date)

    def seed_hierarchical_accounts(self):
        """Seed the chart of accounts with a proper 3-level hierarchical structure."""
        cursor = self.conn.cursor()
        
        # Check if accounts exist
        cursor.execute('SELECT COUNT(*) FROM accounts')
        if cursor.fetchone()[0] > 0:
            # Delete existing accounts
            cursor.execute('DELETE FROM accounts')
            
        # Insert 3-level hierarchical accounts
        # Format: (name, type, code, parent_code, level, is_postable, description)
        accounts = [
            # LEVEL 1: Major Account Types (Non-postable)
            ("Assets", "Asset", "1000", None, 1, 0, "All asset accounts"),
            ("Liabilities", "Liability", "2000", None, 1, 0, "All liability accounts"), 
            ("Equity", "Equity", "3000", None, 1, 0, "All equity accounts"),
            ("Revenue", "Revenue", "4000", None, 1, 0, "All revenue accounts"),
            ("Expenses", "Expense", "5000", None, 1, 0, "All expense accounts"),
            
            # LEVEL 2: Primary Account Categories
            # Assets
            ("Current Assets", "Asset", "1100", "1000", 2, 0, "Assets that can be converted to cash within one year"),
            ("Fixed Assets", "Asset", "1200", "1000", 2, 0, "Long-term assets"),
            ("Other Assets", "Asset", "1300", "1000", 2, 0, "Miscellaneous assets"),
            
            # Liabilities  
            ("Current Liabilities", "Liability", "2100", "2000", 2, 0, "Short-term obligations"),
            ("Long-term Liabilities", "Liability", "2200", "2000", 2, 0, "Long-term debts and obligations"),
            
            # Equity
            ("Owner's Equity", "Equity", "3100", "3000", 2, 1, "Owner's investment and retained earnings"),
            
            # Revenue
            ("Operating Revenue", "Revenue", "4100", "4000", 2, 0, "Revenue from primary business operations"),
            ("Other Revenue", "Revenue", "4200", "4000", 2, 0, "Non-operating revenue"),
            
            # Expenses
            ("Operating Expenses", "Expense", "5100", "5000", 2, 0, "Expenses from primary business operations"),
            ("Administrative Expenses", "Expense", "5200", "5000", 2, 0, "General administrative costs"),
            ("Financial Expenses", "Expense", "5300", "5000", 2, 0, "Interest and financial costs"),
            
            # LEVEL 3: Detailed Sub-accounts (Most are postable)
            # Current Assets
            ("Cash in Hand", "Asset", "1101", "1100", 3, 1, "Physical cash"),
            ("Cash at Bank", "Asset", "1102", "1100", 3, 1, "Bank account balances"),
            ("Petty Cash", "Asset", "1103", "1100", 3, 1, "Small cash fund for minor expenses"),
            ("Accounts Receivable", "Asset", "1111", "1100", 3, 1, "Money owed by customers"),
            ("Notes Receivable", "Asset", "1112", "1100", 3, 1, "Formal written promises to pay"),
            ("Inventory - Raw Materials", "Asset", "1121", "1100", 3, 1, "Raw materials for production"),
            ("Inventory - Work in Process", "Asset", "1122", "1100", 3, 1, "Goods in production"),
            ("Inventory - Finished Goods", "Asset", "1123", "1100", 3, 1, "Completed products ready for sale"),
            ("Prepaid Expenses", "Asset", "1131", "1100", 3, 1, "Expenses paid in advance"),
            
            # Fixed Assets
            ("Land", "Asset", "1201", "1200", 3, 1, "Real estate property"),
            ("Buildings", "Asset", "1202", "1200", 3, 1, "Building structures"),
            ("Equipment", "Asset", "1203", "1200", 3, 1, "Machinery and equipment"),
            ("Vehicles", "Asset", "1204", "1200", 3, 1, "Company vehicles"),
            ("Furniture & Fixtures", "Asset", "1205", "1200", 3, 1, "Office furniture and fixtures"),
            ("Accumulated Depreciation - Buildings", "Asset", "1212", "1200", 3, 1, "Accumulated depreciation on buildings"),
            ("Accumulated Depreciation - Equipment", "Asset", "1213", "1200", 3, 1, "Accumulated depreciation on equipment"),
            
            # Other Assets
            ("Investments", "Asset", "1301", "1300", 3, 1, "Long-term investments"),
            ("Goodwill", "Asset", "1302", "1300", 3, 1, "Intangible asset goodwill"),
            
            # Current Liabilities
            ("Accounts Payable", "Liability", "2101", "2100", 3, 1, "Money owed to suppliers"),
            ("Notes Payable", "Liability", "2102", "2100", 3, 1, "Short-term notes payable"),
            ("Accrued Expenses", "Liability", "2103", "2100", 3, 1, "Expenses incurred but not yet paid"),
            ("Income Tax Payable", "Liability", "2104", "2100", 3, 1, "Income taxes owed"),
            ("Sales Tax Payable", "Liability", "2105", "2100", 3, 1, "Sales taxes collected"),
            ("Employee Benefits Payable", "Liability", "2106", "2100", 3, 1, "Employee benefits owed"),
            
            # Long-term Liabilities
            ("Bank Loan", "Liability", "2201", "2200", 3, 1, "Long-term bank loans"),
            ("Mortgage Payable", "Liability", "2202", "2200", 3, 1, "Mortgage on property"),
            ("Bonds Payable", "Liability", "2203", "2200", 3, 1, "Corporate bonds issued"),
            
            # Owner's Equity
            ("Capital", "Equity", "3101", "3100", 3, 1, "Owner's initial investment"),
            ("Additional Paid-in Capital", "Equity", "3102", "3100", 3, 1, "Additional owner investments"),
            ("Retained Earnings", "Equity", "3103", "3100", 3, 1, "Accumulated profits retained"),
            ("Drawings", "Equity", "3104", "3100", 3, 1, "Owner withdrawals"),
            
            # Operating Revenue
            ("Sales Revenue", "Revenue", "4101", "4100", 3, 1, "Revenue from sales"),
            ("Service Revenue", "Revenue", "4102", "4100", 3, 1, "Revenue from services"),
            ("Rental Revenue", "Revenue", "4103", "4100", 3, 1, "Revenue from rentals"),
            
            # Other Revenue
            ("Interest Income", "Revenue", "4201", "4200", 3, 1, "Interest earned"),
            ("Dividend Income", "Revenue", "4202", "4200", 3, 1, "Dividends received"),
            ("Gain on Asset Sale", "Revenue", "4203", "4200", 3, 1, "Gains from asset sales"),
            
            # Operating Expenses
            ("Cost of Goods Sold", "Expense", "5101", "5100", 3, 1, "Direct costs of products sold"),
            ("Salaries Expense", "Expense", "5102", "5100", 3, 1, "Employee salaries"),
            ("Wages Expense", "Expense", "5103", "5100", 3, 1, "Hourly wages"),
            ("Rent Expense", "Expense", "5104", "5100", 3, 1, "Rental costs"),
            ("Utilities Expense", "Expense", "5105", "5100", 3, 1, "Electricity, water, gas"),
            ("Supplies Expense", "Expense", "5106", "5100", 3, 1, "Office and operating supplies"),
            
            # Administrative Expenses
            ("Office Rent", "Expense", "5201", "5200", 3, 1, "Office rental costs"),
            ("Administrative Salaries", "Expense", "5202", "5200", 3, 1, "Administrative staff salaries"),
            ("Professional Fees", "Expense", "5203", "5200", 3, 1, "Legal and professional fees"),
            ("Insurance Expense", "Expense", "5204", "5200", 3, 1, "Insurance premiums"),
            ("Depreciation Expense", "Expense", "5205", "5200", 3, 1, "Asset depreciation"),
            
            # Financial Expenses
            ("Interest Expense", "Expense", "5301", "5300", 3, 1, "Interest on loans and debt"),
            ("Bank Charges", "Expense", "5302", "5300", 3, 1, "Banking fees and charges"),
            ("Loss on Asset Sale", "Expense", "5303", "5300", 3, 1, "Losses from asset sales"),
        ]
        
        cursor.executemany('INSERT INTO accounts (name, type, code, parent_code, level, is_postable, description) VALUES (?, ?, ?, ?, ?, ?, ?)', accounts)
        self.conn.commit()
        return len(accounts)

    def force_reseed_hierarchical_accounts(self):
        """Force reseed the accounts with proper 3-level hierarchy."""
        cursor = self.conn.cursor()
        # Delete all existing accounts
        cursor.execute('DELETE FROM accounts')
        self.conn.commit()
        
        # Reseed with proper hierarchy
        result = self.seed_hierarchical_accounts()
        print(f"✅ Reseeded {result} accounts with proper 3-level hierarchy")
        return result

    def get_accounts_by_level(self, level=1):
        """Get accounts filtered by hierarchy level (1, 2, or 3)."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, parent_code, level, is_postable, description FROM accounts WHERE level = ? ORDER BY code', (level,))
        return cursor.fetchall()
    
    def get_postable_accounts(self):
        """Get only accounts that can have transactions posted to them."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, parent_code, level, is_postable, description FROM accounts WHERE is_postable = 1 ORDER BY code')
        return cursor.fetchall()
    
    def get_parent_accounts(self, max_level):
        """Get potential parent accounts up to a maximum level."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, parent_code, level, is_postable, description FROM accounts WHERE level <= ? ORDER BY level, code', (max_level,))
        return cursor.fetchall()

    def get_children_accounts(self, parent_code):
        """Get all child accounts of a given parent."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, parent_code, level, is_postable, description FROM accounts WHERE parent_code = ? ORDER BY code', (parent_code,))
        return cursor.fetchall()
    
    def is_account_postable(self, account_name_or_code):
        """Check if an account is postable (can have transactions)."""
        cursor = self.conn.cursor()
        
        # Try by name first
        cursor.execute('SELECT is_postable FROM accounts WHERE name = ?', (account_name_or_code,))
        result = cursor.fetchone()
        
        if not result:
            # Try by code
            cursor.execute('SELECT is_postable FROM accounts WHERE code = ?', (account_name_or_code,))
            result = cursor.fetchone()
            
        return result[0] == 1 if result else False
    
    def get_account_level(self, account_name_or_code):
        """Get the hierarchy level of an account."""
        cursor = self.conn.cursor()
        
        # Try by name first
        cursor.execute('SELECT level FROM accounts WHERE name = ?', (account_name_or_code,))
        result = cursor.fetchone()
        
        if not result:
            # Try by code
            cursor.execute('SELECT level FROM accounts WHERE code = ?', (account_name_or_code,))
            result = cursor.fetchone()
            
        return result[0] if result else None

    def _update_existing_accounts_data(self):
        """Update existing accounts with proper codes, levels, and postable status."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, type, code, level, is_postable FROM accounts')
        accounts = cursor.fetchall()
        
        for name, acc_type, code, level, is_postable in accounts:
            needs_update = False
            new_code = code
            new_level = level
            new_is_postable = is_postable
            
            # Generate code if missing
            if not code:
                new_code = self.generate_account_code(acc_type)
                needs_update = True
            
            # Set proper level and postable status if not set correctly
            if level is None or level == 0 or level == 1:
                # Determine level based on account structure
                if name in ['Assets', 'Liabilities', 'Equity', 'Revenue', 'Expenses']:
                    new_level = 1
                    new_is_postable = 0  # Level 1 accounts are not postable
                elif name in ['Current Assets', 'Fixed Assets', 'Other Assets', 
                             'Current Liabilities', 'Long-term Liabilities', 'Owner\'s Equity',
                             'Operating Revenue', 'Other Revenue', 'Operating Expenses', 
                             'Administrative Expenses', 'Financial Expenses']:
                    new_level = 2
                    new_is_postable = 0  # Most level 2 accounts are headers
                else:
                    new_level = 3
                    new_is_postable = 1  # Level 3 accounts are typically postable
                needs_update = True
                
            if is_postable is None or (new_level == 1 and is_postable == 1):
                new_is_postable = 1 if new_level > 1 else 0
                needs_update = True
            
            if needs_update:
                cursor.execute('UPDATE accounts SET code = ?, level = ?, is_postable = ? WHERE name = ?',                              (new_code, new_level, new_is_postable, name))
        
        self.conn.commit()
