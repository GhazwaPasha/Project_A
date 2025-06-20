# Database Interaction Analysis

## Summary of SQLite Dependencies in Codebase

Based on the analysis of the codebase, here are all the files and components that interact with the SQLite database and will need updates during the PostgreSQL migration:

## Core Database Files (Critical Priority)

### 1. `src/core/accounting_system.py` (1,231 lines)
**Database Operations Found: 51+ instances**

**Key Methods Requiring Updates:**
- `__init__()` - Database initialization and connection setup
- `_setup_connection()` - Connection configuration with SQLite-specific PRAGMA statements
- `refresh_connection()` - Connection management
- `_ensure_connection()` - Connection validation
- `create_tables()` - Table creation with SQLite-specific syntax
- `resolve_account()` - Account search with SQLite-specific queries
- `add_journal_entry()` - Journal entry insertion
- `get_ledger()` - Ledger queries with date filtering
- `get_trial_balance()` - Trial balance calculations
- `generate_income_statement()` - Income statement queries
- `generate_income_statement_breakdown()` - Detailed income statement
- `generate_balance_sheet_breakdown()` - Balance sheet calculations
- `generate_cash_flow_statement()` - Cash flow analysis
- `get_all_accounts()` - Account listing
- `get_account_by_code()` - Account lookup by code
- `add_account()` - Account creation with hierarchy
- `update_account()` - Account modification
- `delete_account()` - Account deletion
- `get_recent_entries()` - Recent entries with pagination
- `search_entries()` - Entry search functionality
- `seed_hierarchical_accounts()` - Account hierarchy seeding
- `begin_transaction()` - Transaction management
- `commit_transaction()` - Transaction commits
- `add_journal_entries_batch()` - Batch operations
- `add_journal_entries_with_progress()` - Batch with progress tracking
- `generate_statement_of_equity()` - Equity statement generation
- `_fuzzy_match_account()` - Account fuzzy matching
- `_find_matching_account()` - Account resolution

**SQLite-Specific Features Used:**
- `PRAGMA synchronous = NORMAL`
- `PRAGMA journal_mode = WAL`
- `PRAGMA cache_size = -2000`
- `PRAGMA temp_store = MEMORY`
- `sqlite_master` table queries
- `ALTER TABLE` statements for schema evolution
- Text-based date storage
- `LIKE` pattern matching for fuzzy search

## Tool Scripts (Medium Priority)

### 2. `tools/export_journal.py` (100 lines)
**Database Operations:**
- Direct SQLite connection
- Journal entry export queries
- Account name processing

**Updates Needed:**
- Replace `sqlite3.connect()` with PostgreSQL connection
- Update query syntax for PostgreSQL
- Handle proper date types

### 3. `tools/generate_entries.py`
**Database Operations:**
- Account selection queries
- Batch journal entry insertion
- Account validation

**Updates Needed:**
- PostgreSQL connection setup
- Batch insert optimization
- Account code handling

### 4. `tools/clear_journal.py`
**Database Operations:**
- Journal entry deletion
- Transaction counting

**Updates Needed:**
- PostgreSQL connection
- Updated query syntax

## UI Components (Low Priority - No Direct DB Access)

The following UI files do not directly access the database but interact with the `AccountingSystem` class:

### 5. UI Pages
- `src/ui/pages/dashboard.py` - Uses accounting system for data display
- `src/ui/pages/journal.py` - Journal entry management
- `src/ui/pages/ledger.py` - Ledger viewing
- `src/ui/pages/trial_balance.py` - Trial balance display
- `src/ui/pages/reports.py` - Report generation
- `src/ui/pages/accounts_hierarchy.py` - Account management
- `src/ui/pages/settings.py` - Configuration (no DB access)

### 6. UI Components
- `src/ui/components/dialogs.py` - Data entry dialogs
- `src/ui/components/widgets.py` - Data display widgets
- `src/ui/components/report_views.py` - Report formatting

**Note:** These files use the `AccountingSystem` class as an interface, so they will automatically work with the new PostgreSQL backend once the core system is migrated.

## Database Schema Analysis

### Current Tables

#### `journal_entries` (869 records)
```sql
CREATE TABLE journal_entries (
    id TEXT PRIMARY KEY,           -- Will become UUID
    date TEXT,                     -- Will become DATE
    description TEXT,              -- Remains TEXT
    debit_account TEXT,            -- Will become VARCHAR with FK
    credit_account TEXT,           -- Will become VARCHAR with FK  
    amount REAL,                   -- Will become DECIMAL(15,2)
    timestamp TEXT                 -- Will become TIMESTAMP WITH TIME ZONE
);
```

#### `accounts` (68 records)
```sql
CREATE TABLE accounts (
    name TEXT PRIMARY KEY,         -- Will become VARCHAR(255) UNIQUE
    type TEXT,                     -- Will become VARCHAR(50) with CHECK constraint
    code TEXT,                     -- Will become VARCHAR(20) UNIQUE
    parent_code TEXT,              -- Will become VARCHAR(20) with FK
    level INTEGER DEFAULT 1,      -- Remains INTEGER with CHECK constraint
    is_postable BOOLEAN DEFAULT 1, -- Remains BOOLEAN
    description TEXT               -- Remains TEXT
);
```

## Migration Impact Assessment

### High Impact Changes (Require Code Updates)
1. **Connection Management** - Complete rewrite needed
2. **Query Syntax** - All SQL queries need PostgreSQL syntax
3. **Data Types** - Date handling, UUID generation, decimal precision
4. **Error Handling** - PostgreSQL-specific error codes and messages
5. **Transaction Management** - Different transaction semantics

### Medium Impact Changes (Configuration Updates)
1. **Environment Configuration** - New connection parameters
2. **Dependencies** - New Python packages (psycopg2, supabase)
3. **Deployment** - New deployment process with Supabase

### Low Impact Changes (Automatic Benefits)
1. **UI Components** - Will work automatically with new backend
2. **Business Logic** - Calculation logic remains the same
3. **File Operations** - Font management, exports remain unchanged

## Migration Strategy Priority

### Phase 1: Core Database Layer (Week 1-2)
- Create `DatabaseManager` class
- Update `AccountingSystem` connection methods
- Migrate basic CRUD operations

### Phase 2: Query Migration (Week 2-3)
- Update all SQL queries for PostgreSQL syntax
- Implement proper data type handling
- Add foreign key constraints

### Phase 3: Advanced Features (Week 3-4)
- Migrate reporting functions
- Update batch operations
- Implement PostgreSQL-specific optimizations

### Phase 4: Testing & Validation (Week 4)
- Data migration validation
- Performance testing
- UI integration testing

## Risk Mitigation

### Data Integrity Risks
- **Risk:** Data loss during migration
- **Mitigation:** Multiple backups, staged migration process, validation scripts

### Performance Risks  
- **Risk:** Slower performance with PostgreSQL
- **Mitigation:** Proper indexing, query optimization, connection pooling

### Compatibility Risks
- **Risk:** Breaking changes in UI functionality
- **Mitigation:** Maintain same interface in `AccountingSystem` class

## Success Metrics

### Technical Metrics
- All 51+ database operations successfully migrated
- No data loss (869 journal entries, 68 accounts preserved)
- Query performance maintained or improved
- Zero breaking changes in UI functionality

### Business Metrics
- All financial calculations remain accurate
- All reports generate correctly
- User workflow unchanged
- Enhanced scalability for future growth

This analysis confirms that while the migration requires significant work in the core database layer (`accounting_system.py`), the well-structured architecture means that UI components will continue to work without changes once the core migration is complete.
