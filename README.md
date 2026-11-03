# Accountuitive

Web-first accounting and financial management: multi-tenant organizations, role-based access, reporting, inventory, vouchers, and suppliers. The product UI is a **Vite and React** app in `web/`. **Next.js** at the repository root hosts the API, authentication and the MCP server, and serves the built UI from `public/app`.

## Repository layout

```
Project_A/
├── src/           # Next.js application source (App Router)
├── public/        # Static assets for Next.js
├── database/      # SQL schema, migrations, and report function definitions
├── scripts/       # Node SQL helpers (scripts/js/*.mjs)
├── services/      # Placeholder for future APIs (see services/README.md)
├── shared/        # Shared assets and documentation
└── tools/         # Optional development tools
```

## Technology stack (web)

- **Framework**: Next.js 14, React 18, TypeScript  
- **Styling**: Tailwind CSS, Radix UI  
- **State**: Zustand  
- **Data**: TanStack Query, Supabase client  

## Configuration

1. Copy [.env.example](.env.example) to `.env` at the **repository root**. Optional overrides: `.env.local`, `.env.development.local`, etc.  
2. Never commit real secrets. If keys were ever committed in history, rotate them.

## Quick start (web)

```bash
npm install
npm run dev
```

## Database and scripts

SQL artifacts live in [database/](database/). Node helpers that share `DATABASE_URL` with the app live in [scripts/js/](scripts/js/) (for example `npm run db:apply-inventory`).

## Development

**Web app**

- `npm run dev` — development server  
- `npm run build` — production build  
- `npm run lint` — ESLint  

## License

This project is licensed under the MIT License.
