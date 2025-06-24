# 🚀 AI Accountant - Multi-Tenant SaaS Platform

A modern, multi-organization accounting application with Supabase authentication and role-based access control.

## 🎯 Quick Start

### **Recommended: Smart Launcher**
```bash
python run.py
```
- Automatically detects configuration
- Multi-tenant mode when Supabase is configured
- Single-tenant fallback mode when not configured

### **Alternative Entry Points**
```bash
# Full multi-tenant with authentication
python main_auth.py

# Original single-tenant mode (backward compatible)
python main.py
```

## 📁 Project Structure

```
Project_A/
├── run.py                          # ⭐ Smart launcher (recommended)
├── main_auth.py                    # Multi-tenant with authentication
├── main.py                         # Original single-tenant mode
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── MULTITENANT_SETUP.md           # Detailed setup instructions
├── src/
│   ├── core/
│   │   ├── auth_manager.py         # Supabase authentication
│   │   ├── session_manager.py     # User sessions & permissions
│   │   ├── supabase_offline_manager.py # Main backend with offline support
│   │   └── enhanced_accounting_system.py # Enhanced features
│   └── ui/
│       ├── auth/
│       │   ├── login_window.py     # Modern login dialog
│       │   ├── signup_dialog.py   # User registration
│       │   └── organization_selector.py # Org picker
│       ├── components/             # UI components
│       ├── pages/                  # Application pages
│       └── mainwindow.py          # Main application window
├── tools/
│   ├── setup_multitenant.py       # Database migration script
│   ├── create_multitenant_schema.sql # SQL migration
│   └── setup_local_postgres.py    # Local database setup
└── assets/                         # Icons and fonts
```

## ✨ Features

### **Multi-Tenant Architecture**
- 🏢 **Organization-based isolation** - Complete data separation
- 👥 **Multi-user support** - Users can belong to multiple organizations
- 🔐 **Role-based access control** - 4 permission levels
- 🔒 **Row Level Security** - Database-level data protection

### **Authentication System**
- 🎨 **Modern glassmorphism UI** - Beautiful, responsive design
- ✅ **Complete signup flow** - User registration with organization creation
- 🔑 **Supabase Auth integration** - Enterprise-grade authentication
- 📧 **Email verification** - Secure account activation
- 🏭 **Organization management** - Create or join organizations

### **User Roles**
| Role | Permissions |
|------|-------------|
| **Super Admin** | Full system access, manage all organizations |
| **Organization Owner** | Full organization control, billing, user management |
| **Organization Admin** | User management, settings, no billing |
| **Accountant** | Accounting operations, reports, no user management |

## 🛠️ Setup

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit .env with your Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### 3. **Setup Database** (Optional - for multi-tenant features)
```bash
python tools/setup_multitenant.py
```

### 4. **Run Application**
```bash
python run.py
```

## 🎪 Usage Modes

### **Smart Mode** (Recommended)
- Automatically detects Supabase configuration
- Enables multi-tenant features when configured
- Falls back to single-tenant when not configured
- Best for both development and production

### **Multi-Tenant Mode**
- Full authentication with login/signup
- Organization management
- Role-based permissions
- Data isolation between organizations

### **Single-Tenant Mode**
- Traditional single-user accounting
- Local database only
- No authentication required
- Perfect for personal use

## 🔧 Development

### **Environment Variables**
```bash
# Required for multi-tenant mode
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Optional
LOCAL_POSTGRES_HOST=localhost
LOCAL_POSTGRES_DB=accounting_local
MISTRAL_API_KEY=your-api-key
```

### **Database Schema**
- Organizations, users, roles, organization_members tables
- Updated accounts and journal_entries with organization context
- Row Level Security policies for data isolation
- Audit trails with created_by/updated_by fields

## 🚀 Production Deployment

1. **Setup Supabase project**
2. **Run database migration**
3. **Configure environment variables**
4. **Deploy with `python run.py`**

## 📖 Documentation

- `MULTITENANT_SETUP.md` - Complete multi-tenant setup guide
- Inline code documentation
- Type hints throughout codebase

## 🎉 What's New

✅ **Complete signup system** with organization creation  
✅ **Modern authentication UI** with glassmorphism design  
✅ **Smart launcher** that adapts to configuration  
✅ **Clean project structure** with unnecessary files removed  
✅ **Production-ready** multi-tenant architecture  

---

**🎊 Your single-tenant accounting app is now a full multi-tenant SaaS platform!**

Start with: `python run.py`
