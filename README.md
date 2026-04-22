# Accountuitive

Web-first accounting and financial management: multi-tenant organizations, role-based access, reporting, inventory, vouchers, and suppliers. The product UI is the **Next.js** app in `web-app/`.

## Repository layout

```
Project_A/
├── web-app/       # Next.js application (primary product)
├── database/      # SQL schema, migrations, and report function definitions
├── scripts/       # Python setup and maintenance utilities
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

1. Copy [.env.example](.env.example) to `.env` at the **repository root** (and configure `web-app` env files as documented in the web app, if applicable).  
2. Never commit real secrets. If keys were ever committed in history, rotate them in the Supabase (and other) dashboards.

## Quick start (web)

```bash
cd web-app
npm install
npm run dev
```

## Database and scripts

SQL artifacts live in [database/](database/). Python utilities (Supabase setup, migrations helpers, etc.) live in [scripts/](scripts/). Install Python dependencies from the repo root:

```bash
pip install -r requirements.txt
```

Examples (run from repository root so paths resolve correctly):

```bash
python scripts/setup_multitenant.py
python scripts/manage_super_admin.py
```

Use `POSTGRES_*` or `DB_*` variables from `.env.example` depending on the script.

## Development

**Web app**

- `npm run dev` — development server  
- `npm run build` — production build  
- `npm run lint` — ESLint  

## License

This project is licensed under the MIT License.
