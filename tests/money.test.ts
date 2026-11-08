import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { roundMoney, sumMoney, toCents } from '../src/lib/money'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { BooksServiceAdmin as B } from '../src/server/books/service'

test('money is added in whole cents, so long sums are exact', () => {
  assert.equal(0.1 + 0.2 === 0.3, false, 'plain floating point is not exact')
  assert.equal(sumMoney([0.1, 0.2]), 0.3)
  assert.equal(sumMoney(Array(1000).fill(0.1)), 100)
  assert.equal(toCents('1234567.895'), 123456790, 'text is read exactly and rounds half up')
  assert.equal(roundMoney(1.005), 1.01)
  assert.equal(roundMoney(-2.675), -2.68)
  assert.throws(() => toCents('ten'), /not an amount/)
})

let db: Awaited<ReturnType<typeof startDatabase>>
before(async () => { db = await startDatabase() })
after(async () => { await db.stop() })

test('many small entries keep the books and statements exact', () => actingUserStore.run(USER, async () => {
  const bank = await account('1010', 'Bank', 'asset')
  const sales = await account('4000', 'Sales', 'revenue')
  for (let i = 0; i < 30; i++) {
    await D.createJournalEntry(
      { organization_id: ORG, entry_number: '', entry_date: '2026-05-01', description: 'Small sale', reference: null, total_amount: 0, is_posted: true, created_by: USER, posted_by: USER, posted_at: null } as never,
      [{ account_id: bank, description: null, debit_amount: 0.1, credit_amount: 0, line_order: 1 }, { account_id: sales, description: null, debit_amount: 0, credit_amount: 0.1, line_order: 2 }] as never,
    )
  }
  const is = await D.generateIncomeStatement(ORG, '2026-05-01', '2026-05-31')
  assert.equal(is.revenue.total, 3)
  const bs = await D.generateBalanceSheet(ORG, '2026-05-31')
  assert.equal(bs.totalAssets, 3)
  assert.ok(bs.isBalanced)
  // A voucher amount column is an exact decimal now.
  const [t] = await db.sql`SELECT data_type FROM information_schema.columns WHERE table_name = 'inventory_vouchers' AND column_name = 'deposit_amount'`
  assert.equal(t.data_type, 'numeric')
  assert.ok((await B.getCashFlow(ORG, '2026-05-01', '2026-05-31')).agrees)
}))
