"""
Enhanced Database Schema with Audit Trails, Foreign Keys, and Period Closing
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
import logging
from typing import List, Dict, Optional, Tuple, Any

class EnhancedDatabaseSchema:
    """Enhanced database schema with audit trails and period closing."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def create_enhanced_tables(self):
        """Create enhanced tables with audit trails and period closing."""
        enhanced_tables_sql = """
        -- Audit log table for tracking all changes
        CREATE TABLE IF NOT EXISTS audit_log (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            table_name VARCHAR(50) NOT NULL,
            record_id UUID NOT NULL,
            operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
            old_values JSONB,
            new_values JSONB,
            changed_by UUID,
            changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            session_id VARCHAR(100),
            ip_address INET,
            user_agent TEXT
        );
        
        -- Period closing table for formal accounting periods
        CREATE TABLE IF NOT EXISTS accounting_periods (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            period_name VARCHAR(50) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            period_type VARCHAR(20) DEFAULT 'MONTHLY' CHECK (period_type IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY')),
            status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'LOCKED')),
            closed_by UUID,
            closed_at TIMESTAMP WITH TIME ZONE,
            trial_balance_checksum VARCHAR(64),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(start_date, end_date, period_type)
        );
        
        -- Budget management tables
        CREATE TABLE IF NOT EXISTS budgets (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            budget_name VARCHAR(100) NOT NULL,
            fiscal_year INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'APPROVED', 'ACTIVE', 'LOCKED')),
            created_by UUID,
            approved_by UUID,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS budget_lines (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            budget_id UUID REFERENCES budgets(id) ON DELETE CASCADE,
            account_code VARCHAR(20) NOT NULL,
            account_name VARCHAR(255) NOT NULL,
            period_month INTEGER CHECK (period_month BETWEEN 1 AND 12),
            budgeted_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(budget_id, account_code, period_month)
        );
        
        -- Enhanced journal entries with approval workflow
        CREATE TABLE IF NOT EXISTS journal_entry_headers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            entry_number VARCHAR(20) UNIQUE NOT NULL,
            entry_date DATE NOT NULL,
            period_id UUID REFERENCES accounting_periods(id),
            description TEXT NOT NULL,
            reference_number VARCHAR(50),
            source_document VARCHAR(100),
            total_amount DECIMAL(15,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PENDING', 'APPROVED', 'POSTED', 'REVERSED')),
            created_by UUID,
            approved_by UUID,
            posted_by UUID,
            reversed_by UUID,
            reversal_reason TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            approved_at TIMESTAMP WITH TIME ZONE,
            posted_at TIMESTAMP WITH TIME ZONE,
            reversed_at TIMESTAMP WITH TIME ZONE
        );
        
        CREATE TABLE IF NOT EXISTS journal_entry_lines (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            header_id UUID REFERENCES journal_entry_headers(id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL,
            account_code VARCHAR(20) NOT NULL,
            account_name VARCHAR(255) NOT NULL,
            debit_amount DECIMAL(15,2) DEFAULT 0 CHECK (debit_amount >= 0),
            credit_amount DECIMAL(15,2) DEFAULT 0 CHECK (credit_amount >= 0),
            description TEXT,
            cost_center VARCHAR(50),
            project_code VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(header_id, line_number),
            CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0))
        );
        
        -- Cash flow classification table
        CREATE TABLE IF NOT EXISTS cash_flow_classifications (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            account_code VARCHAR(20) NOT NULL,
            cash_flow_category VARCHAR(20) NOT NULL CHECK (cash_flow_category IN ('OPERATING', 'INVESTING', 'FINANCING')),
            subcategory VARCHAR(50),
            is_cash_account BOOLEAN DEFAULT FALSE,
            effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
            effective_to DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(account_code, effective_from)
        );
        
        -- Financial ratios and KPIs tracking
        CREATE TABLE IF NOT EXISTS financial_ratios (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            ratio_name VARCHAR(50) NOT NULL,
            ratio_category VARCHAR(30) NOT NULL CHECK (ratio_category IN ('LIQUIDITY', 'PROFITABILITY', 'EFFICIENCY', 'LEVERAGE')),
            calculation_method TEXT NOT NULL,
            target_value DECIMAL(10,4),
            warning_threshold DECIMAL(10,4),
            critical_threshold DECIMAL(10,4),
            is_higher_better BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS financial_ratio_values (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            ratio_id UUID REFERENCES financial_ratios(id) ON DELETE CASCADE,
            period_id UUID REFERENCES accounting_periods(id),
            calculated_value DECIMAL(10,4) NOT NULL,
            variance_from_target DECIMAL(10,4),
            status VARCHAR(20) DEFAULT 'NORMAL' CHECK (status IN ('NORMAL', 'WARNING', 'CRITICAL')),
            calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(ratio_id, period_id)
        );
        
        -- Document attachments for journal entries
        CREATE TABLE IF NOT EXISTS document_attachments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            entity_type VARCHAR(50) NOT NULL,
            entity_id UUID NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_size BIGINT,
            mime_type VARCHAR(100),
            uploaded_by UUID,
            uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            description TEXT
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at);
        CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);
        
        CREATE INDEX IF NOT EXISTS idx_accounting_periods_dates ON accounting_periods(start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_accounting_periods_status ON accounting_periods(status);
        
        CREATE INDEX IF NOT EXISTS idx_journal_headers_date ON journal_entry_headers(entry_date);
        CREATE INDEX IF NOT EXISTS idx_journal_headers_status ON journal_entry_headers(status);
        CREATE INDEX IF NOT EXISTS idx_journal_headers_period ON journal_entry_headers(period_id);
        
        CREATE INDEX IF NOT EXISTS idx_journal_lines_header ON journal_entry_lines(header_id);
        CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_entry_lines(account_code);
        
        CREATE INDEX IF NOT EXISTS idx_cash_flow_account ON cash_flow_classifications(account_code);
        CREATE INDEX IF NOT EXISTS idx_cash_flow_category ON cash_flow_classifications(cash_flow_category);
        
        CREATE INDEX IF NOT EXISTS idx_attachments_entity ON document_attachments(entity_type, entity_id);
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(enhanced_tables_sql)
            self.logger.info("Enhanced database tables created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create enhanced tables: {e}")
            raise
    
    def create_audit_triggers(self):
        """Create audit triggers for automatic change tracking."""
        audit_triggers_sql = """
        -- Create audit trigger function
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO audit_log (table_name, record_id, operation, new_values)
                VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW));
                RETURN NEW;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values)
                VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW));
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                INSERT INTO audit_log (table_name, record_id, operation, old_values)
                VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD));
                RETURN OLD;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Create triggers for key tables
        DROP TRIGGER IF EXISTS audit_accounts ON accounts;
        CREATE TRIGGER audit_accounts
            AFTER INSERT OR UPDATE OR DELETE ON accounts
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
            
        DROP TRIGGER IF EXISTS audit_journal_entries ON journal_entries;
        CREATE TRIGGER audit_journal_entries
            AFTER INSERT OR UPDATE OR DELETE ON journal_entries
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
            
        DROP TRIGGER IF EXISTS audit_journal_headers ON journal_entry_headers;
        CREATE TRIGGER audit_journal_headers
            AFTER INSERT OR UPDATE OR DELETE ON journal_entry_headers
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
            
        DROP TRIGGER IF EXISTS audit_journal_lines ON journal_entry_lines;
        CREATE TRIGGER audit_journal_lines
            AFTER INSERT OR UPDATE OR DELETE ON journal_entry_lines
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(audit_triggers_sql)
            self.logger.info("Audit triggers created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create audit triggers: {e}")
            raise
    
    def add_foreign_key_constraints(self):
        """Add proper foreign key constraints with enhanced referential integrity."""
        fk_sql = """
        -- Add foreign key constraints to existing tables
        DO $$ 
        BEGIN
            -- Accounts parent-child relationship
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_accounts_parent_code') THEN
                ALTER TABLE accounts 
                ADD CONSTRAINT fk_accounts_parent_code 
                FOREIGN KEY (parent_code) REFERENCES accounts(code)
                ON DELETE SET NULL ON UPDATE CASCADE;
            END IF;
            
            -- Journal entries to accounts (if using account names)
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_journal_debit_account') THEN
                -- Note: This assumes account names are unique and stable
                -- Consider using account codes instead for better referential integrity
                ALTER TABLE journal_entries 
                ADD CONSTRAINT fk_journal_debit_account 
                FOREIGN KEY (debit_account_name) REFERENCES accounts(name)
                ON DELETE RESTRICT ON UPDATE CASCADE;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_journal_credit_account') THEN
                ALTER TABLE journal_entries 
                ADD CONSTRAINT fk_journal_credit_account 
                FOREIGN KEY (credit_account_name) REFERENCES accounts(name)
                ON DELETE RESTRICT ON UPDATE CASCADE;
            END IF;
            
            -- Enhanced journal entry relationships
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_budget_lines_budget') THEN
                ALTER TABLE budget_lines 
                ADD CONSTRAINT fk_budget_lines_budget 
                FOREIGN KEY (budget_id) REFERENCES budgets(id)
                ON DELETE CASCADE;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                          WHERE constraint_name = 'fk_ratio_values_ratio') THEN
                ALTER TABLE financial_ratio_values 
                ADD CONSTRAINT fk_ratio_values_ratio 
                FOREIGN KEY (ratio_id) REFERENCES financial_ratios(id)
                ON DELETE CASCADE;
            END IF;
        END $$;
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(fk_sql)
            self.logger.info("Foreign key constraints added successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add foreign key constraints: {e}")
            raise
    
    def initialize_cash_flow_classifications(self):
        """Initialize default cash flow classifications for common accounts."""
        classifications = [
            # Operating Activities
            ('4101', 'OPERATING', 'Revenue from Operations'),
            ('4102', 'OPERATING', 'Service Revenue'),
            ('5101', 'OPERATING', 'Cost of Goods Sold'),
            ('5102', 'OPERATING', 'Salaries and Wages'),
            ('5104', 'OPERATING', 'Rent Expense'),
            ('5105', 'OPERATING', 'Utilities'),
            ('2101', 'OPERATING', 'Accounts Payable'),
            ('1111', 'OPERATING', 'Accounts Receivable'),
            ('1121', 'OPERATING', 'Inventory'),
            
            # Investing Activities
            ('1201', 'INVESTING', 'Land Purchases'),
            ('1202', 'INVESTING', 'Building Investments'),
            ('1203', 'INVESTING', 'Equipment Purchases'),
            ('1301', 'INVESTING', 'Long-term Investments'),
            
            # Financing Activities
            ('2201', 'FINANCING', 'Long-term Debt'),
            ('2202', 'FINANCING', 'Mortgage Financing'),
            ('3101', 'FINANCING', 'Owner Capital'),
            ('3104', 'FINANCING', 'Owner Withdrawals'),
            
            # Cash Accounts
            ('1101', 'OPERATING', 'Cash in Hand'),
            ('1102', 'OPERATING', 'Cash at Bank'),
            ('1103', 'OPERATING', 'Petty Cash'),
        ]
        
        insert_sql = """
        INSERT INTO cash_flow_classifications (account_code, cash_flow_category, subcategory, is_cash_account)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (account_code, effective_from) DO NOTHING
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                for code, category, subcategory in classifications:
                    is_cash = code in ['1101', '1102', '1103']
                    cursor.execute(insert_sql, (code, category, subcategory, is_cash))
            
            self.logger.info("Cash flow classifications initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize cash flow classifications: {e}")
            raise
    
    def setup_default_financial_ratios(self):
        """Set up default financial ratios for monitoring."""
        ratios = [
            # Liquidity Ratios
            ('Current Ratio', 'LIQUIDITY', 'current_assets / current_liabilities', 2.0, 1.5, 1.0, True),
            ('Quick Ratio', 'LIQUIDITY', '(current_assets - inventory) / current_liabilities', 1.0, 0.8, 0.5, True),
            ('Cash Ratio', 'LIQUIDITY', 'cash / current_liabilities', 0.2, 0.15, 0.1, True),
            
            # Profitability Ratios
            ('Gross Profit Margin', 'PROFITABILITY', '(revenue - cogs) / revenue * 100', 30.0, 20.0, 10.0, True),
            ('Net Profit Margin', 'PROFITABILITY', 'net_income / revenue * 100', 10.0, 5.0, 0.0, True),
            ('Return on Assets', 'PROFITABILITY', 'net_income / total_assets * 100', 8.0, 5.0, 2.0, True),
            
            # Efficiency Ratios
            ('Asset Turnover', 'EFFICIENCY', 'revenue / average_total_assets', 1.5, 1.0, 0.5, True),
            ('Inventory Turnover', 'EFFICIENCY', 'cogs / average_inventory', 6.0, 4.0, 2.0, True),
            ('Receivables Turnover', 'EFFICIENCY', 'revenue / average_receivables', 12.0, 8.0, 4.0, True),
            
            # Leverage Ratios
            ('Debt to Equity', 'LEVERAGE', 'total_liabilities / total_equity', 1.0, 1.5, 2.0, False),
            ('Debt Ratio', 'LEVERAGE', 'total_liabilities / total_assets', 0.4, 0.6, 0.8, False),
            ('Interest Coverage', 'LEVERAGE', 'ebit / interest_expense', 5.0, 3.0, 1.5, True),
        ]
        
        insert_sql = """
        INSERT INTO financial_ratios (ratio_name, ratio_category, calculation_method, 
                                    target_value, warning_threshold, critical_threshold, is_higher_better)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ratio_name) DO NOTHING
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.executemany(insert_sql, ratios)
            
            self.logger.info("Default financial ratios set up")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set up financial ratios: {e}")
            raise
