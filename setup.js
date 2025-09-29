#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🚀 Setting up Accountuitive Web...\n');

// Check if .env.local exists
const envPath = path.join(process.cwd(), '.env.local');
if (!fs.existsSync(envPath)) {
  console.log('❌ .env.local not found. Please create it with your Supabase credentials.');
  console.log('   Copy .env.example to .env.local and add your Supabase URL and key.\n');
  process.exit(1);
}

// Check if node_modules exists
const nodeModulesPath = path.join(process.cwd(), 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
  console.log('📦 Installing dependencies...');
  console.log('   Run: npm install\n');
}

console.log('✅ Setup complete!');
console.log('\n📋 Next steps:');
console.log('1. Run: npm install');
console.log('2. Run: npm run dev');
console.log('3. Open: http://localhost:3000');
console.log('\n🎉 Your React web app is ready!');
