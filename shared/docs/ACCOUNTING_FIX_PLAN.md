# Accounting fix plan

**Status:** phases 1 to 5 were done in November 2026, with tests in `tests/statements`, `ledger-integrity`, `classification`, `controls` and `agent-proposals`. The section at the end lists what's left.

From the November 2026 audit. Each phase lands with tests on the in-memory database, built from a worked example whose right answers are worked out by hand.

**The worked example:**
- Owner capital 10,000, a bank loan of 5,000, cash sales of 3,000.
- A refund of 500 to Sales returns, rent of 1,000, and a gain of 200 credited to an expense account.
- Right answers: revenue 2,500, expenses 800, net income 1,700. Assets 16,500, liabilities 4,800, equity 11,700, so the balance sheet balances.

## Phase 1: correct reports

1. One function computes balances for every report. It uses each account's natural direction (assets and expenses: debits minus credits; the rest: credits minus debits). It includes inactive accounts that still hold a balance, and counts posted entries only.
2. Income statement: signed amounts, never absolute values. A contra account, such as Sales returns, reduces its section. With no dates, it covers the month so far.
3. Balance sheet:
   - Liabilities and equity use credit minus debit.
   - Two computed equity lines: **Current year earnings** (profit from 1 January of the as-of year) and **Retained earnings, prior years** (all earlier profit).
   - These replace year-end closing entries. The books stay correct without a closing step, the way most current small-business ledgers work.
   - It balances to the cent.
4. Dashboard figures and ratios come from the same balances. No `Math.abs` or `Math.max(0)`. Current ratio, quick ratio and gross margin are worked out from the categories.
5. The trial balance takes an as-of date. The agent's tool passes it through.
6. The balance-sheet screen shows subsections and child accounts. It shows liabilities and equity as positive figures, plus the two computed earnings lines.
7. Remove the empty aged-receivables and aged-payables stubs in DataService. `BooksService.getAgedReport` is the real one.

## Phase 2: ledger integrity

1. Validation refuses negative or non-numeric amounts.
2. Migration 013:
   - Amounts can't be negative, and a line can't be both a debit and a credit.
   - Entry numbers are unique per organization.
   - The database checks that each entry balances, at the end of the transaction that writes it.
   - Posted amounts, accounts, dates and organization can't be changed or deleted. Who created or posted an entry can still be relinked.
   - New columns `source` and `source_id` record where an entry came from: manual, invoice, payment, agent, MCP and so on.
3. The server numbers journal entries (`JE-0001` and on) when the caller doesn't give a number. Numbers sent by the browser or the agent are ignored.
4. Accounts:
   - An account that still holds a balance can't be made inactive.
   - An account that has entries can't change type.

## Phase 3: classification

Migration 014 adds to `accounts`:
- `system_role`: the job the account does, unique per organization. One of receivable, payable, inventory, received-not-billed, output tax, input tax, retained earnings, cash, bank, purchase price variance or opening balance.
- `is_control`: the account belongs to a subledger, so manual entries can't post to it.
- `cash_flow_category`: cash, operating, investing or financing.
- `pl_category`: operating, investing, financing or income tax, the IFRS 18 categories in force from 2027.
- `is_contra`: the account reduces its section, like Sales returns or Accumulated depreciation.

Reports use these fields:
- The cash flow finds cash through `cash_flow_category = 'cash'`, falling back to the name match only when nothing is tagged.
- Borrowings are financing.
- The income statement adds an operating-profit subtotal.

When it runs, the migration sets these for accounts the system already uses: receivable accounts on customers, payable mappings, inventory accounts on categories, the received-not-billed account, and tax rate accounts.

## Phase 4: subledger controls

1. Manual and agent entries can't post to control accounts. Payments, invoices, stock and the other services can.
2. A control-account check compares, for any date:
   - Receivables in the ledger with open invoices, and payables with open bills.
   - Inventory in the ledger with stock value.
   - Received-not-billed in the ledger with receipts not yet billed.

   It's part of the close checklist, in place of the debits-equal-credits check that always passes, and it's available to the agent.
3. A payment must go to an asset account and can't be dated before its document.

## Phase 5: the agent

1. Proposals have a type: `journal`, `payment` or `post_document`. Approval runs the same service the screens use, so a payment updates the invoice and the receivables subledger.
2. New tools:
   - `find_open_documents`, to find an open invoice or bill.
   - `propose_payment`, `propose_post_document` and `get_control_check`.
   - `get_trial_balance` with an as-of date.
3. The instructions route each event to the right tool. A raw journal is only for something no document records.
4. Checks before any proposal exists:
   - Control accounts are refused.
   - A likely duplicate (same amount and accounts within 7 days, posted or pending) is refused.
   - Debiting a revenue account or crediting an expense account produces a warning on the proposal.
5. Entries record whether they came from the agent or MCP.

## Second pass

Done the same month:
- **Exact money:** sums are added in whole cents (`src/lib/money.ts`), and migration 017 turns the last floating-point money columns into exact decimals.
- **Document numbers:** invoice and bill numbers are assigned at posting. Drafts are numbered DRAFT-<id>.
- **Price differences:** a bill from goods receipts clears "received, not billed" at the received price, and any difference goes to the purchase price differences account.
- **Credit vouchers:** a purchase voucher on credit raises a posted bill that shares the voucher's entry (migration 016).
- **Second approver:** an optional setting. When it's on, the person who asked the agent can't approve, and MCP apps can't record directly.
- **Starter chart:** a classified starter chart is added when an organization is created, or from the empty Accounts page.

## Still open

- **Tax returns:** recording a return doesn't post the settlement entry or lock the period's documents. Set aside on purpose.
- **Fiscal years:** only calendar years are supported. The balance sheet's "current year" starts on 1 January.
- **Stock at the right cost:** price differences are expensed in full, even when some of the goods are still in stock.
