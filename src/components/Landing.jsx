/**
 * Landing Page Component
 * ----------------------
 * This component renders the public landing page for the TradeSphere application.
 * It highlights the product value proposition and provides entry points
 * for authentication (Login / Signup).
 *
 * Tech Stack:
 * - React (Functional Component)
 * - Tailwind CSS (Styling)
 * - lucide-react (Icons)
 *
 * Props:
 * @param {Function} onLoginClick  - Callback triggered when user clicks Login
 * @param {Function} onSignupClick - Callback triggered when user clicks Signup
 */

import { TrendingUp, Shield, Zap, BarChart3 } from 'lucide-react'

function Landing({ onLoginClick, onSignupClick }) {
  return (
    /**
     * Root container
     * - Full viewport height
     * - Dark gradient background
     * - Vertical layout using flexbox
     */
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white flex flex-col">

      {/* ================= HEADER ================= */}
      <header className="px-6 py-6 border-b border-gray-800">
        <div className="max-w-6xl mx-auto flex items-center justify-between">

          {/* Logo + Branding */}
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-opacity-20 rounded-2xl flex items-center justify-center">
              <img src="Stock.png" alt="Logo" className="w-10 h-10 object-contain rounded-1xl" />
            </div>
            <div>
              <p className="text-sm uppercase tracking-widest text-gray-400">
                Virtual Trading Suite
              </p>
              <h1 className="text-3xl font-bold">TradeSphere</h1>
            </div>
          </div>

          {/* Auth Buttons (hidden on small screens) */}
          <div className="space-x-4 hidden sm:flex">
            <button
              onClick={onLoginClick}
              className="px-5 py-2 rounded-lg border border-gray-700 text-gray-200 hover:border-gray-500 transition"
            >
              Log In
            </button>

            <button
              onClick={onSignupClick}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 font-semibold"
            >
              Sign Up
            </button>
          </div>
        </div>
      </header>

      {/* ================= MAIN CONTENT ================= */}
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-6 py-16 grid gap-12 lg:grid-cols-[1.1fr_0.9fr] items-center">

          {/* -------- Left: Marketing Copy -------- */}
          <div className="space-y-8">

            {/* Tagline Badge */}
            <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full border border-gray-700 text-sm text-gray-300">
              <span className="w-2 h-2 rounded-full bg-green-400"></span>
              <span>Elevate your trading instincts</span>
            </div>

            {/* Headline + Description */}
            <div className="space-y-6">
              <h2 className="text-4xl sm:text-5xl font-bold leading-tight">
                Simulate real markets. Sharpen your strategy. Grow smarter every session.
              </h2>
              <p className="text-lg text-gray-300">
                TradeSphere delivers an immersive trading arena with ₹50,000 virtual capital,
                live-style pricing, recovery boosts, and a dynamic portfolio tracker.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <button
                onClick={onSignupClick}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold"
              >
                Start with ₹50,000
              </button>

              <button
                onClick={onLoginClick}
                className="px-6 py-3 border border-gray-700 rounded-xl text-gray-200 hover:border-gray-500"
              >
                I already have an account
              </button>
            </div>

            {/* Metrics / Highlights */}
            <div className="grid grid-cols-3 gap-6 text-center">
              <div className="bg-gray-800 bg-opacity-60 rounded-2xl p-4">
                <p className="text-sm text-gray-400">Starting Capital</p>
                <p className="text-2xl font-bold text-green-400">₹50,000</p>
              </div>
              <div className="bg-gray-800 bg-opacity-60 rounded-2xl p-4">
                <p className="text-sm text-gray-400">Recovery Boost</p>
                <p className="text-2xl font-bold text-blue-400">₹5,000/day</p>
              </div>
              <div className="bg-gray-800 bg-opacity-60 rounded-2xl p-4">
                <p className="text-sm text-gray-400">Live Strategies</p>
                <p className="text-2xl font-bold text-purple-400">24/7</p>
              </div>
            </div>
          </div>

          {/* -------- Right: Feature Panel -------- */}
          <div className="bg-gray-900/80 border border-gray-800 rounded-3xl p-10 space-y-10">

            {/* Section Header */}
            <div className="space-y-4">
              <p className="text-sm uppercase tracking-[0.3em] text-gray-500">
                Why TradeSphere
              </p>
              <h3 className="text-3xl font-semibold">
                Built for fearless experimentation
              </h3>
            </div>

            {/* Feature List */}
            <div className="space-y-6">
              {[
                {
                  title: 'Guided trading missions',
                  description:
                    'Complete risk-free missions that mirror real market setups.',
                  icon: Zap
                },
                {
                  title: 'Portfolio depth & analytics',
                  description:
                    'Visualize holdings, exposure, and rebalance instantly.',
                  icon: BarChart3
                },
                {
                  title: 'Secure practice environment',
                  description:
                    'Layered protections keep your learning progress safe.',
                  icon: Shield
                }
              ].map(feature => {
                const Icon = feature.icon
                return (
                  <div key={feature.title} className="flex items-start space-x-4">
                    <div className="w-12 h-12 rounded-2xl bg-gray-800 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-lg">{feature.title}</p>
                      <p className="text-gray-400 text-sm mt-1">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </main>

      {/* ================= FOOTER ================= */}
      <footer className="px-6 py-6 border-t border-gray-800 text-sm text-gray-500 text-center">
        Trusted by aspiring traders • Learn, iterate, and graduate to live markets
      </footer>
    </div>
  )
}

export default Landing