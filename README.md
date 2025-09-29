# 🚀 Accountuitive - Multi-Platform Accounting System

A modern, multi-platform accounting and financial management system with both web and desktop applications.

## 📁 Project Structure

```
Project_A/
├── 📁 web-app/          # Next.js React Web Application
├── 📁 desktop-app/      # PyQt6 Desktop Application  
├── 📁 backend/          # Backend Services & Database
├── 📁 shared/           # Shared Resources
├── 📁 tools/            # Development Tools
└── 📁 tests/            # Test Files
```

## 🛠️ Technology Stack

### Web App (React/Next.js)
- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS, Radix UI
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Animations**: Framer Motion

### Desktop App (PyQt6)
- **Frontend**: PyQt6 with custom UI components
- **Backend**: Supabase (PostgreSQL) with Row Level Security
- **Offline Support**: SQLite local cache
- **AI Integration**: Natural language processing

### Backend
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Multi-tenant**: Organization-based data isolation
- **API**: FastAPI (optional)

## 🚀 Quick Start

### Web Application
```bash
cd web-app
npm install
npm run dev
```

### Desktop Application
```bash
cd desktop-app
pip install -r requirements.txt
python run.py
```

### Backend Services
```bash
cd backend
pip install -r requirements.txt
# Run database migrations
python scripts/setup_multitenant.py
```

## ✨ Features

- **Multi-Tenant Architecture** - Organization-based data isolation
- **Role-Based Access Control** - 4 permission levels
- **Modern UI** - Glassmorphism design with dark theme
- **Responsive Design** - Mobile-first approach
- **Real-time Updates** - Supabase integration
- **Financial Reporting** - Comprehensive accounting reports
- **AI Integration** - Natural language processing for transactions
- **Offline Support** - Desktop app with local caching

## 📱 Platforms

- **Web**: Any modern browser
- **Desktop**: Windows, macOS, Linux
- **Mobile**: Responsive web design

## 🔐 Authentication

- Email/password login
- Multi-tenant organization support
- Role-based access control
- Session management

## 📊 Development

### Available Scripts

**Web App:**
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

**Desktop App:**
- `python run.py` - Start desktop application
- `python build_exe.py` - Build executable

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ using Next.js, PyQt6, and Supabase**