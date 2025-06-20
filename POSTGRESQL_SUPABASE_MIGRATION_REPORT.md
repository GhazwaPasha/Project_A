# PostgreSQL + Supabase Migration Report

## Executive Summary

This report outlines the migration plan for the PyQt6 Accounting Application from SQLite to PostgreSQL with Supabase as the backend-as-a-service provider. The application currently has 869 journal entries and 68 accounts in the SQLite database.

## Current Architecture Analysis

### Database Schema Overview

**Current Tables:**
1. **journal_entries** (869 records)
   - id (TEXT PRIMARY KEY)
   - date (TEXT)
   - description (TEXT)
   - debit_account (TEXT)
   - credit_account (TEXT)
   - amount (REAL)
   - timestamp (TEXT)

2. **accounts** (68 records)
   - name (TEXT PRIMARY KEY)
   - type (TEXT)
   - code (TEXT)
   - parent_code (TEXT)
   - level (INTEGER DEFAULT 1)
   - is_postable (BOOLEAN DEFAULT 1)
   - description (TEXT)

### Current Database Access Patterns

**Main Database Operations (from `accounting_system.py`):**
- Connection management with SQLite-specific optimizations (WAL mode, cache settings)
- Account resolution with fuzzy matching and search capabilities
- Journal entry CRUD operations with batch processing
- Financial reporting queries (trial balance, income statement, balance sheet)
- Hierarchical account management with parent-child relationships

## Migration Strategy

### Phase 1: Schema Translation

#### PostgreSQL Schema Definition

```sql
-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Accounts table with enhanced structure
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Income', 'Expense')),
    code VARCHAR(20) UNIQUE,
    parent_code VARCHAR(20),
    level INTEGER DEFAULT 1 CHECK (level > 0),
    is_postable BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraint for hierarchical structure
    CONSTRAINT fk_parent_code FOREIGN KEY (parent_code) REFERENCES accounts(code)
);

-- Journal entries table with improved data types
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    debit_account_name VARCHAR(255) NOT NULL,
    credit_account_name VARCHAR(255) NOT NULL,
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints for data integrity
    CONSTRAINT fk_debit_account FOREIGN KEY (debit_account_name) REFERENCES accounts(name),
    CONSTRAINT fk_credit_account FOREIGN KEY (credit_account_name) REFERENCES accounts(name)
);

-- Indexes for performance
CREATE INDEX idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX idx_journal_entries_debit_account ON journal_entries(debit_account_name);
CREATE INDEX idx_journal_entries_credit_account ON journal_entries(credit_account_name);
CREATE INDEX idx_accounts_code ON accounts(code);
CREATE INDEX idx_accounts_parent_code ON accounts(parent_code);
CREATE INDEX idx_accounts_type ON accounts(type);

-- Updated_at triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journal_entries_updated_at BEFORE UPDATE ON journal_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Phase 2: Code Changes Required

#### 2.1 Database Connection Layer

**New Dependencies (requirements.txt):**
```
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
PyQt6-sip==13.6.0
openai==1.12.0
requests==2.31.0
pandas>=2.0.0
psycopg2-binary>=2.9.0
supabase>=2.0.0
python-dotenv>=1.0.0
```

**New Configuration File (`config.py`):**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Direct PostgreSQL connection (for advanced operations)
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
```

**Environment Variables (`.env`):**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
POSTGRES_HOST=db.your-project.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

#### 2.2 Database Access Layer Redesign

**New `database_manager.py`:**
```python
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from typing import List, Dict, Optional, Tuple
import uuid
from datetime import datetime, date
from config import DatabaseConfig

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(
            DatabaseConfig.SUPABASE_URL, 
            DatabaseConfig.SUPABASE_KEY
        )
        self._pg_conn = None
    
    def get_pg_connection(self):
        """Get direct PostgreSQL connection for complex operations."""
        if not self._pg_conn or self._pg_conn.closed:
            self._pg_conn = psycopg2.connect(
                host=DatabaseConfig.POSTGRES_HOST,
                port=DatabaseConfig.POSTGRES_PORT,
                database=DatabaseConfig.POSTGRES_DB,
                user=DatabaseConfig.POSTGRES_USER,
                password=DatabaseConfig.POSTGRES_PASSWORD,
                cursor_factory=RealDictCursor
            )
        return self._pg_conn
    
    def close_connection(self):
        """Close PostgreSQL connection."""
        if self._pg_conn and not self._pg_conn.closed:
            self._pg_conn.close()
```

#### 2.3 Major Code Changes in `accounting_system.py`

**Key Areas Requiring Updates:**

1. **Connection Management:**
   - Replace `sqlite3.connect()` with Supabase client and PostgreSQL connections
   - Remove SQLite-specific PRAGMA statements
   - Implement connection pooling for better performance

2. **Query Syntax Changes:**
   ```python
   # OLD (SQLite)
   cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
   
   # NEW (PostgreSQL)
   cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='accounts'")
   ```

3. **Data Type Handling:**
   ```python
   # OLD - TEXT dates
   date_str = "2024-01-15"
   
   # NEW - Proper DATE types
   from datetime import date
   entry_date = date(2024, 1, 15)
   ```

4. **UUID Handling:**
   ```python
   # OLD
   entry_id = str(uuid.uuid4())
   
   # NEW - Let PostgreSQL generate UUIDs
   # Or use proper UUID types in Python
   import uuid
   entry_id = uuid.uuid4()
   ```

### Phase 3: Supabase Integration Benefits

#### 3.1 Real-time Features
- Enable real-time subscriptions for live data updates
- Multi-user support with conflict resolution
- Automatic data synchronization across clients

#### 3.2 Authentication & Security
- Built-in user authentication system
- Row-level security (RLS) policies
- Role-based access control

#### 3.3 API Layer
- Automatic REST API generation
- GraphQL support
- Real-time subscriptions via WebSockets

### Phase 4: Data Migration Plan

#### 4.1 Export Current Data
```python
# Use existing export_journal.py as base
# Export to CSV format for easy import
```

#### 4.2 Data Cleaning & Transformation
1. **Date Conversion:** Convert TEXT dates to proper DATE types
2. **Amount Precision:** Ensure decimal precision is maintained
3. **Account Validation:** Verify all account references are valid
4. **UUID Generation:** Generate new UUIDs for existing records

#### 4.3 Import Process
```sql
-- Sample import script
COPY accounts(name, type, code, parent_code, level, is_postable, description)
FROM '/path/to/accounts.csv'
DELIMITER ','
CSV HEADER;

COPY journal_entries(entry_date, description, debit_account_name, credit_account_name, amount)
FROM '/path/to/journal_entries.csv'
DELIMITER ','
CSV HEADER;
```

### Phase 5: Performance Optimizations

#### 5.1 Query Optimization
- Use prepared statements for frequent queries
- Implement proper indexing strategy
- Utilize PostgreSQL's advanced features (CTEs, window functions)

#### 5.2 Connection Management
- Implement connection pooling
- Use async operations where appropriate
- Optimize batch operations

### Phase 6: Testing Strategy

#### 6.1 Data Integrity Testing
- Verify all migrated data matches original
- Test account hierarchy relationships
- Validate financial calculations

#### 6.2 Performance Testing
- Compare query performance SQLite vs PostgreSQL
- Test with larger datasets
- Measure application startup time

#### 6.3 Feature Testing
- Test all existing functionality
- Verify reports generate correctly
- Test concurrent access scenarios

## Implementation Timeline

### Week 1: Setup & Configuration
- Set up Supabase project
- Configure database schema
- Set up development environment

### Week 2: Core Migration
- Implement new database layer
- Migrate core accounting operations
- Update connection management

### Week 3: Feature Updates
- Update all CRUD operations
- Migrate reporting functionality
- Update UI components for new data flows

### Week 4: Testing & Optimization
- Comprehensive testing
- Performance optimization
- Data migration and validation

## Risk Assessment & Mitigation

### High Risks
1. **Data Loss During Migration**
   - *Mitigation:* Multiple backups, staged migration process
2. **Performance Degradation**
   - *Mitigation:* Thorough performance testing, query optimization
3. **Breaking Changes in UI**
   - *Mitigation:* Incremental migration, extensive testing

### Medium Risks
1. **Learning Curve for Team**
   - *Mitigation:* Training, documentation, gradual adoption
2. **Increased Hosting Costs**
   - *Mitigation:* Cost analysis, optimization strategies

## Post-Migration Benefits

### Immediate Benefits
- Better data integrity with foreign key constraints
- Improved performance with proper indexing
- Better concurrent access support
- Automatic backups via Supabase

### Long-term Benefits
- Scalability for multi-user scenarios
- Real-time collaboration features
- Cloud-based accessibility
- Advanced reporting capabilities with PostgreSQL features

### Future Enhancement Opportunities
- Web-based interface using Supabase APIs
- Mobile app development
- Advanced analytics and reporting
- Integration with external accounting systems

## Conclusion

The migration from SQLite to PostgreSQL + Supabase represents a significant upgrade that will provide better performance, scalability, and feature capabilities. While the migration requires substantial code changes, the long-term benefits justify the investment. The phased approach minimizes risks and ensures a smooth transition.

The current codebase has 51+ database operations that need updating, but the well-structured `accounting_system.py` makes this migration manageable. With proper planning and testing, this migration will position the application for future growth and enhanced capabilities.
