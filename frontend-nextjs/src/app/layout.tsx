import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { 
  Home, 
  BarChart3, 
  Building,
  User, 
  Bell,
  Search,
  Menu,
  Zap,
  Brain
} from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Climatize AI Agent",
  description: "Revolutionary multi-agent AI platform for solar project financing",
};

function Navigation() {
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-gray-900">Climatize</span>
                <span className="text-xs text-green-600 font-medium ml-1">AI</span>
              </div>
            </Link>

            {/* Main Navigation */}
            <div className="hidden md:ml-10 md:flex md:space-x-8">
              <Link 
                href="/" 
                className="text-gray-500 hover:text-green-600 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <Home className="w-4 h-4 mr-2" />
                Home
              </Link>
              
              <Link 
                href="/dashboard" 
                className="text-gray-500 hover:text-green-600 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Dashboard
              </Link>
              
              <Link 
                href="/issuer-portal" 
                className="text-gray-500 hover:text-green-600 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <Building className="w-4 h-4 mr-2" />
                Issuer Portal
              </Link>
            </div>
          </div>

          {/* Ultrathink Status Indicator */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-full border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <Brain className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-700">Ultrathink Active</span>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search projects..."
                className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* Notifications */}
            <button className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 rounded-lg">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User Menu */}
            <div className="relative">
              <button className="flex items-center space-x-2 p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 rounded-lg">
                <User className="w-5 h-5" />
                <span className="text-sm font-medium text-gray-700">Admin</span>
              </button>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button className="p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 rounded-lg">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold">Climatize</span>
                <span className="text-green-400 font-medium ml-1">AI Agent</span>
              </div>
            </div>
            <p className="text-gray-400 mb-4 max-w-md">
              Revolutionary multi-agent AI platform for solar project financing. 
              Our collaborative agents deliver superior investment decisions through 
              advanced LangGraph architecture.
            </p>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <Brain className="w-4 h-4 text-green-400" />
              <span>Powered by Ultrathink Multi-Agent Framework</span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Platform</h3>
            <ul className="space-y-2">
              <li><Link href="/dashboard" className="text-gray-400 hover:text-green-400 transition-colors">Dashboard</Link></li>
              <li><Link href="/issuer-portal" className="text-gray-400 hover:text-green-400 transition-colors">Issuer Portal</Link></li>
              <li><Link href="/projects" className="text-gray-400 hover:text-green-400 transition-colors">Projects</Link></li>
              <li><Link href="/analytics" className="text-gray-400 hover:text-green-400 transition-colors">Analytics</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Technology</h3>
            <ul className="space-y-2">
              <li><span className="text-gray-400">LangChain + LangGraph</span></li>
              <li><span className="text-gray-400">Next.js 14+ App Router</span></li>
              <li><span className="text-gray-400">Azure Functions</span></li>
              <li><span className="text-gray-400">OpenAI GPT-4</span></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">
            © 2024 Climatize AI Agent. All rights reserved.
          </p>
          <div className="mt-4 md:mt-0 flex space-x-6">
            <Link href="/privacy" className="text-gray-400 hover:text-green-400 text-sm transition-colors">Privacy</Link>
            <Link href="/terms" className="text-gray-400 hover:text-green-400 text-sm transition-colors">Terms</Link>
            <Link href="/security" className="text-gray-400 hover:text-green-400 text-sm transition-colors">Security</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Navigation />
          <main className="flex-1">
            {children}
          </main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
