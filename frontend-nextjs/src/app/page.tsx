"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Zap, Brain, TrendingUp, Shield, CheckCircle, Star } from "lucide-react";

export default function Home() {
  const [isUltrathinkExpanded, setIsUltrathinkExpanded] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-16">
        <div className="absolute inset-0 bg-gradient-to-r from-green-600/10 to-emerald-600/5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-6">
              <Zap className="w-4 h-4 mr-2" />
              Powered by Ultrathink AI Framework
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              <span className="text-green-600">Climatize</span>
              <br />
              <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                AI Agent
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-4xl mx-auto leading-relaxed">
              Revolutionary multi-agent AI platform for solar project financing. 
                             Our agents <span className="text-green-600 font-semibold">&ldquo;bounce ideas off each other&rdquo;</span> using 
              advanced LangGraph architecture for superior investment decisions.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Link 
                href="/dashboard"
                className="group px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl text-lg font-semibold transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 flex items-center"
              >
                Launch Platform
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              
              <Link 
                href="/issuer-portal"
                className="px-8 py-4 border-2 border-green-600 text-green-600 hover:bg-green-600 hover:text-white rounded-xl text-lg font-semibold transition-all duration-300"
              >
                Issuer Portal
              </Link>
              
              <button 
                onClick={() => setIsUltrathinkExpanded(!isUltrathinkExpanded)}
                className="px-8 py-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-lg font-semibold transition-all duration-300 flex items-center"
              >
                <Brain className="mr-2 w-5 h-5" />
                Explore Ultrathink
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">40%</div>
                <div className="text-sm text-gray-600">Better Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">85%</div>
                <div className="text-sm text-gray-600">Time Savings</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">60%</div>
                <div className="text-sm text-gray-600">Risk Reduction</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">4</div>
                <div className="text-sm text-gray-600">AI Agents</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ultrathink Framework Expansion */}
      {isUltrathinkExpanded && (
        <section className="py-16 bg-white border-t border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                🧠 Ultrathink Multi-Agent Framework
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Advanced collaborative AI that thinks like a team of experts
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200">
                <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Brain className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Agent Collaboration</h3>
                <p className="text-gray-600">
                  Multiple specialized AI agents work together, challenging assumptions 
                  and building on shared insights for superior analysis.
                </p>
              </div>
              
              <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
                <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Shield className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Conflict Resolution</h3>
                <p className="text-gray-600">
                  When agents disagree, our Ultrathink supervisor facilitates discussion 
                  and generates collaborative solutions.
                </p>
              </div>
              
              <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200">
                <div className="w-16 h-16 bg-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Superior Decisions</h3>
                <p className="text-gray-600">
                  By bouncing ideas between agents, we achieve 40% better investment 
                  decision accuracy compared to single-agent analysis.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Features Grid */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Platform Capabilities
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Complete solar project financing platform powered by collaborative AI
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-200">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Project Analysis</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Comprehensive technical, regulatory, and financial analysis with multi-agent collaboration.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-200">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-6">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Issuer Portal</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Complete capital raising platform with investor communication and payment tracking.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-200">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mb-6">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">AI Orchestration</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                LangGraph-powered multi-agent system with supervisor-router pattern for optimal decisions.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-200">
              <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center mb-6">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Portfolio Management</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Real-time portfolio tracking with performance analytics and risk assessment.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Modern Technology Stack
            </h2>
            <p className="text-xl text-gray-600">
              Built with cutting-edge technologies for enterprise-scale deployment
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-2xl mb-6">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Frontend</h3>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Next.js 14+ with App Router
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  TypeScript & Tailwind CSS
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Modern React Patterns
                </li>
              </ul>
            </div>
            
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-2xl mb-6">
                <span className="text-2xl">🧠</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">AI & Backend</h3>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  LangChain + LangGraph
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Azure Functions Python
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  OpenAI GPT-4 Integration
                </li>
              </ul>
            </div>
            
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-2xl mb-6">
                <span className="text-2xl">☁️</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Infrastructure</h3>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Docker + Terraform
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Azure Cloud Platform
                </li>
                <li className="flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  Cosmos DB + Redis
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Performance Metrics */}
      <section className="py-20 bg-gradient-to-r from-green-600 to-emerald-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-white">
            <h2 className="text-4xl font-bold mb-4">
              Proven Results
            </h2>
            <p className="text-xl text-green-100 mb-12 max-w-3xl mx-auto">
              Real performance improvements from our Ultrathink multi-agent framework
            </p>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-5xl font-bold text-white mb-2">40%</div>
                <div className="text-green-100 mb-4">Better Decision Accuracy</div>
                <div className="w-full bg-green-700 rounded-full h-2">
                  <div className="bg-white h-2 rounded-full" style={{width: '80%'}}></div>
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-5xl font-bold text-white mb-2">85%</div>
                <div className="text-green-100 mb-4">Analysis Time Reduction</div>
                <div className="w-full bg-green-700 rounded-full h-2">
                  <div className="bg-white h-2 rounded-full" style={{width: '85%'}}></div>
                </div>
              </div>
              
              <div className="text-center">
                <div className="text-5xl font-bold text-white mb-2">60%</div>
                <div className="text-green-100 mb-4">Risk Blind Spots Eliminated</div>
                <div className="w-full bg-green-700 rounded-full h-2">
                  <div className="bg-white h-2 rounded-full" style={{width: '75%'}}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-20 bg-gray-900">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Experience 
            <span className="text-green-400"> Ultrathink AI</span>?
          </h2>
          <p className="text-xl text-gray-300 mb-10">
            Join the future of solar project financing with collaborative AI agents that think together.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/dashboard"
              className="group px-10 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl text-lg font-semibold transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 flex items-center justify-center"
            >
              Start Free Trial
              <Star className="ml-2 w-5 h-5" />
            </Link>
            
            <Link 
              href="/demo"
              className="px-10 py-4 border-2 border-gray-600 text-gray-300 hover:bg-gray-800 hover:border-gray-500 rounded-xl text-lg font-semibold transition-all duration-300"
            >
              Request Demo
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
