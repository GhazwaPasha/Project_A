# Accountuitive

Web-first accounting and financial management: multi-tenant organizations, role-based access, reporting, inventory, vouchers, and suppliers. The product UI is a **Vite and React** app in `web/`. **Next.js** at the repository root hosts the API, authentication and the MCP server, and serves the built UI from `public/app`.

## Repository layout

```
Project_A/
├── web/       # The web app: Vite and React. Builds into public/app
├── src/       # The server: Next.js route handlers and services
├── database/  # SQL migrations (database/migrations_v2), applied in number order
├── tests/     # Runs on an in-memory Postgres, never a real database
├── scripts/   # Node SQL helpers (scripts/js/*.mjs)
└── shared/    # Design and workflow notes (shared/docs)
```

## Technology stack

- **Web app**: Vite, React 19, TanStack Router, TanStack Query, Tailwind CSS 4, shadcn/ui on Base UI  
- **Server**: Next.js 16 route handlers, TypeScript, Neon Postgres, Neon Auth  
- **Agent**: any OpenAI-compatible model, set with `GOOGLE_AI_KEY` or `ANYROUTER_API_KEY`, or `AGENT_PROVIDER`, `AGENT_MODEL`, `AGENT_API_KEY` and `AGENT_BASE_URL`  

## Configuration

1. Copy [.env.example](.env.example) to `.env` at the **repository root**. Optional overrides: `.env.local`, `.env.development.local`, etc.  
2. Never commit real secrets. If keys were ever committed in history, rotate them.

## Quick start (web)

```bash
npm install
npm --prefix web install
npm run dev
npm run dev:web
```

## Database and scripts

SQL artifacts live in [database/](database/). Node helpers that share `DATABASE_URL` with the app live in [scripts/js/](scripts/js/) (for example `npm run db:apply-inventory`).

## Development

**Web app**

- `npm run dev` — API server  
- `npm run dev:web` — web app development server  
- `npm run build` — builds the web app, then the server  
- `npm test` — accounting rules and service tests, on a throwaway in-memory Postgres using the real migrations  

## Known limitations

**Not built yet**

- Two-factor sign-in and automatic backups.
- Fiscal year handling: reports use calendar periods, so the setting is hidden until it does something.
- Low cash alerts: the setting is hidden for the same reason.
- Recurring invoices and multiple currencies.

**Works, with limits**

- **AI data privacy:** the agent is running on Google's free tier. Google's terms say not to send sensitive or confidential information to unpaid services, reviewers may read it, and it may be used to improve Google's products. Unpaid services also can't be offered to users in the EEA, UK or Switzerland. Move to a paid key before taking on real customers.
- **AnyRouter:** its no-data-collection filter leaves no free provider available, so `anyrouter/free` fails while the filter is on. Removing the filter would send data to providers that may collect it.
- **Invites aren't emailed:** the app has no email service, so an owner sends the invite link themselves.
- **Password reset:** Neon sends the email. A live reset email hasn't been confirmed yet, and the site's domain may need adding to Neon's allowed list.
- **Credit notes can't be undone:** re-invoice instead. A credit on a bill made from goods received reduces the "received, not billed" account and leaves stock as it is.
- **Cash flow finds cash accounts by name:** an asset counts as cash if its name includes cash or bank, or if it has an imported statement. The report lists the accounts it used.
- **Audit log:** it records successful changes made through the app, the agent and connected AI. It doesn't record failed attempts or direct database changes, and a failure to write an entry is logged on the server but doesn't undo the change.
- **FIFO:** cost layers are per item, not per warehouse, and a backdated purchase doesn't recalculate costs already issued. A FIFO bill can't be voided once any of its stock has been used.
- **Stock counts on serial items:** a shortage removes the oldest units. Use a stock movement to write off specific ones.
- **Tracking and builds:** an item tracks batches or serial numbers, not both. Builds run one level at a time, so sub-assemblies are built first.
- **Secrets in old history:** old commits may stay reachable by direct link until GitHub Support purges them. The leaked keys have been rotated.

## License

This project is licensed under the MIT License.
