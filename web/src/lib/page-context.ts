export type PageContext = { title: string; url: string; filters: string[]; text: string }

const clean = (s: string) => s.replace(/[ \t]+/g, ' ').replace(/\n{2,}/g, '\n').trim()

/** Reads what the person can see right now, so the agent can answer about "this". */
export function readPage(): PageContext {
  const main = document.querySelector('main')
  const hide = (text: string, root: Element) => {
    let out = text
    root.querySelectorAll<HTMLElement>('[data-agent-private]').forEach((el) => { if (el.innerText) out = out.replace(el.innerText, '[hidden]') })
    return out
  }
  // innerText skips anything not on screen, such as other pages of a long list.
  const page = main ? clean(hide(main.innerText, main)) : ''
  const dialog = [...document.querySelectorAll('[role=dialog]')].at(-1) as HTMLElement | undefined
  const open = dialog ? clean(hide(dialog.innerText, dialog)).slice(0, 2500) : ''
  const chips = [...document.querySelectorAll<HTMLElement>('main button[aria-pressed=true]')].map((b) => clean(b.innerText))
  const fields = [...document.querySelectorAll<HTMLInputElement>('main input[aria-label^="Search"], main input[type=date]')]
    .filter((i) => i.value)
    .map((i) => `${i.getAttribute('aria-label')}: ${i.value}`)
  return {
    title: clean(dialog?.querySelector('h2')?.textContent ?? main?.querySelector('h1')?.textContent ?? '').slice(0, 200),
    url: `${location.pathname}${location.search}`.slice(0, 300),
    filters: [...chips, ...fields].slice(0, 20).map((f) => f.slice(0, 100)),
    text: `${open ? `Open dialog:\n${open}\n\nPage behind it:\n` : ''}${page}`.slice(0, 8000),
  }
}

const BY_PAGE: [RegExp, string[]][] = [
  [/^\/home/, ['What needs my attention first?', 'How am I doing this month?', 'Where can I save money?']],
  [/^\/journal/, ['Do any of these entries look wrong?', 'Summarize recent activity']],
  [/^\/ledger\/./, ['Explain this account', 'Why did this balance change?', 'Does anything here look unusual?']],
  [/^\/ledger/, ['Which of these accounts look unusual?', 'Where is most of my money?']],
  [/^\/trial-balance/, ['Do my books look right?', 'Explain these checks']],
  [/^\/accounts/, ['Is anything missing from these accounts?', 'Which accounts could I merge?']],
  [/^\/reports\/income-statement/, ['Explain this report', 'What is my biggest cost?', 'How can I improve my profit?']],
  [/^\/reports\/aged/, ['Who should I deal with first?', 'What is most overdue?']],
  [/^\/reports\/balance-sheet/, ['Explain this report', 'Is my business in a healthy position?']],
  [/^\/reports/, ['Summarize these reports', 'Compare this year with last year']],
  [/^\/inventory\/vouchers|^\/approvals/, ['What should I decide first?', 'Explain what is waiting here']],
  [/^\/inventory\/items\//, ['Explain this item', 'When should I reorder this?', 'Does anything look unusual?']],
  [/^\/inventory\/warehouses/, ['Is my stock in the right places?', 'What is each warehouse holding?']],
  [/^\/inventory\/purchase-orders/, ['What is late?', 'What still needs a bill?', 'Draft a purchase order for me']],
  [/^\/inventory\/assemblies/, ['What can I build right now?', 'Which parts are holding me back?']],
  [/^\/inventory\/counts/, ['Which differences are worth checking?', 'What should I count next?']],
  [/^\/inventory\/planner/, ['What should I order first?', 'Which items could run out?']],
  [/^\/inventory\/reports/, ['Where is money tied up?', 'Which items should I stop stocking?', 'Do my stock and books agree?']],
  [/^\/inventory/, ['What should I reorder first?', 'What is tying up the most money?']],
  [/^\/invoices/, ['Who owes me the most?', 'Which invoices are overdue?', 'Draft an invoice for me']],
  [/^\/bills/, ['Which bills should I pay first?', 'What is due this month?', 'Draft a bill for me']],
  [/^\/customers/, ['Who owes me the most?', 'Summarize these customers']],
  [/^\/banking/, ['What is left to sort out here?', 'Does anything look unusual?']],
  [/^\/budgets/, ['How am I doing against budget?', 'Help me set a budget from last year']],
  [/^\/forecast/, ['Will I have enough cash?', 'What should I watch out for?']],
  [/^\/tax/, ['Explain my tax position', 'Is anything missing tax?']],
  [/^\/close/, ['Am I ready to close this period?', 'What does closing do?']],
  [/^\/suppliers/, ['Who do I owe the most?', 'Summarize these suppliers']],
]

/** Starting points that fit the page the person is on. */
export const suggestionsFor = (path: string) => BY_PAGE.find(([re]) => re.test(path))?.[1] ?? ['Explain this page', 'What can you help me with?']
