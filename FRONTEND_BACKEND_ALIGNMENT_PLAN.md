# Frontend-Backend Alignment Fix Plan

## Current Issues Identified

### 1. ✅ RESOLVED: Single Workspace Switcher 
- **WorkspaceSwitcher** (bottom bar only): Uses `session_manager.get_available_organizations()`
- Removed duplicate/redundant switchers (OrganizationSwitcher, CompactWorkspaceSwitcher)

### 2. Data Loading Inconsistencies
- Different methods to get organization data
- Different organization type detection logic
- Inconsistent session manager integration

### 3. Missing UI Updates
- Organization changes don't properly refresh all UI components
- Session manager changes don't trigger UI updates
- Navigation visibility not properly updated

## Fix Plan

### Phase 1: Standardize Data Access
1. **Ensure all components use `auth_manager.get_user_organizations()`**
2. **Use `session_manager` for active organization management**
3. **Standardize organization type detection**

### Phase 2: Fix Main Window Integration
1. **Properly connect organization switcher signals**
2. **Update navigation visibility on organization changes**
3. **Ensure all pages receive organization context updates**

### Phase 3: Cleanup and Consolidation
1. **Remove duplicate organization switcher components**
2. **Consolidate organization type detection logic**
3. **Ensure consistent UI behavior**

### Phase 4: Testing and Verification
1. **Test user signup and organization creation**
2. **Test organization switching**
3. **Test role-based navigation visibility**
4. **Test personal vs team organization handling**

## Implementation Steps

### Step 1: Fix WorkspaceSwitcher Component
- Standardize data loading methods
- Fix organization type detection
- Ensure proper session manager integration

### Step 2: Update Main Window
- Connect workspace switcher signals properly
- Update navigation when organization changes
- Refresh organization-dependent UI elements

### Step 3: Cleanup Organization Components
- Remove unused organization switcher variants
- Consolidate into single, consistent component
- Update all references

### Step 4: Test End-to-End
- Verify organization loading after login
- Test organization switching functionality
- Verify role-based UI updates
