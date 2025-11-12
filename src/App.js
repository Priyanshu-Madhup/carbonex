import React, { useEffect, useState } from 'react';
import './App.css';
import Login from './components/Login';
import Signup from './components/Signup';
import OrganizationSetup from './components/OrganizationSetup';
import Recommendations from './components/Recommendations';
import Dashboard from './components/Dashboard';
import logoImage from './assets/carbonex.png';

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showOrgSetup, setShowOrgSetup] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const [user, setUser] = useState(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (showProfileDropdown && !event.target.closest('.profile-dropdown')) {
        setShowProfileDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfileDropdown]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleSignupSuccess = () => {
    // After successful signup, redirect to login page
    setShowSignup(false);
    setShowLogin(true);
  };

  const handleLogout = () => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch('http://localhost:8000/api/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setShowProfileDropdown(false);
  };

  return (
    <div className="App">
      {/* Show Dashboard if activated */}
      {showDashboard ? (
        <Dashboard
          user={user}
          sessionToken={localStorage.getItem('token')}
          onNavigateToDashboard={() => { setShowDashboard(true); setShowRecommendations(false); setShowOrgSetup(false); }}
          onNavigateToRecommendations={() => { setShowRecommendations(true); setShowDashboard(false); setShowOrgSetup(false); }}
          onNavigateToOrgSetup={() => { setShowOrgSetup(true); setShowDashboard(false); setShowRecommendations(false); }}
          onNavigateToHome={() => { setShowDashboard(false); setShowRecommendations(false); setShowOrgSetup(false); }}
          onBack={() => setShowDashboard(false)}
          onLogout={handleLogout}
        />
      ) : /* Show Recommendations if activated */
      showRecommendations ? (
        <Recommendations
          user={user}
          onNavigateToDashboard={() => { setShowDashboard(true); setShowRecommendations(false); setShowOrgSetup(false); }}
          onNavigateToRecommendations={() => { setShowRecommendations(true); setShowDashboard(false); setShowOrgSetup(false); }}
          onNavigateToOrgSetup={() => { setShowOrgSetup(true); setShowDashboard(false); setShowRecommendations(false); }}
          onNavigateToHome={() => { setShowDashboard(false); setShowRecommendations(false); setShowOrgSetup(false); }}
          onBack={() => setShowRecommendations(false)}
          onLogout={handleLogout}
        />
      ) : /* Show Organization Setup if activated */
      showOrgSetup ? (
        <OrganizationSetup
          user={user}
          onNavigateToDashboard={() => { setShowDashboard(true); setShowRecommendations(false); setShowOrgSetup(false); }}
          onNavigateToRecommendations={() => { setShowRecommendations(true); setShowDashboard(false); setShowOrgSetup(false); }}
          onNavigateToOrgSetup={() => { setShowOrgSetup(true); setShowDashboard(false); setShowRecommendations(false); }}
          onNavigateToHome={() => { setShowDashboard(false); setShowRecommendations(false); setShowOrgSetup(false); }}
          onComplete={() => setShowOrgSetup(false)}
          onBack={() => setShowOrgSetup(false)}
          onLogout={handleLogout}
        />
      ) : (
        <>
          {/* Auth Modals */}
          {showLogin && (
            <Login
              onClose={() => setShowLogin(false)}
              onSwitchToSignup={() => {
                setShowLogin(false);
                setShowSignup(true);
              }}
              onLoginSuccess={handleLoginSuccess}
            />
          )}
          {showSignup && (
            <Signup
              onClose={() => setShowSignup(false)}
              onSwitchToLogin={() => {
                setShowSignup(false);
                setShowLogin(true);
              }}
              onSignupSuccess={handleSignupSuccess}
            />
          )}

          {/* Header / Navbar */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <img src={logoImage} alt="CarbonEx" className="logo-image" />
            <span className="logo-text">CarbonEx</span>
          </div>
          <div className="nav-links">
            {user ? (
              <>
                <a href="#dashboard" className="nav-tab" onClick={(e) => { e.preventDefault(); setShowDashboard(true); setShowRecommendations(false); setShowOrgSetup(false); }}>
                  Dashboard
                </a>
                <a href="#recommendations" className="nav-tab" onClick={(e) => { e.preventDefault(); setShowRecommendations(true); setShowDashboard(false); setShowOrgSetup(false); }}>
                  Recommendations
                </a>
                <a href="#organization" className="nav-tab" onClick={(e) => { e.preventDefault(); setShowOrgSetup(true); setShowDashboard(false); setShowRecommendations(false); }}>
                  Organization Setup
                </a>
                <a href="#settings" className="nav-tab">Settings</a>
                <a href="#help" className="nav-tab">Help / Docs</a>
                <div className="profile-dropdown">
                  <span 
                    className="user-icon" 
                    title={user.name}
                    onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                  >
                    👤
                  </span>
                  {showProfileDropdown && (
                    <div className="dropdown-menu">
                      <div className="dropdown-header">
                        <div className="dropdown-user-name">{user.name}</div>
                        <div className="dropdown-user-email">{user.email}</div>
                      </div>
                      <div className="dropdown-divider"></div>
                      <button className="dropdown-item" onClick={handleLogout}>
                        <span className="dropdown-icon">🚪</span>
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <a href="#home">Home</a>
                <a href="#features">Features</a>
                <a href="#dashboard">Dashboard</a>
                <button className="login-btn" onClick={() => setShowLogin(true)}>Login</button>
                <button className="signup-btn" onClick={() => setShowSignup(true)}>Signup</button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-background">
          <div className="gradient-orb orb-1"></div>
          <div className="gradient-orb orb-2"></div>
          <div className="gradient-orb orb-3"></div>
        </div>
        <div className="hero-container">
          <div className="hero-left">
            <div className="hero-badge">
              <span className="badge-text">AI-Powered Carbon Management</span>
            </div>
            <h1 className="hero-title">
              Monitor. Predict. <span className="highlight-text">Reduce.</span>
            </h1>
            <p className="hero-subtitle">
              Empowering organizations to achieve net-zero through intelligent AI-driven 
              analytics and actionable sustainability insights.
            </p>
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-number">500+</div>
                <div className="stat-label">Organizations</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-number">2M+</div>
                <div className="stat-label">Tons CO₂ Reduced</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-number">98%</div>
                <div className="stat-label">Accuracy</div>
              </div>
            </div>
          </div>
          <div className="hero-right">
            <div className="dashboard-illustration">
              <div className="dash-card">
                <div className="dash-header">
                  <span>Carbon Analytics</span>
                  <span className="status-badge">Live</span>
                </div>
                <div className="dash-chart">
                  <div className="chart-bar" style={{height: '60%'}}>
                    <div className="chart-tooltip">-12%</div>
                  </div>
                  <div className="chart-bar" style={{height: '40%'}}>
                    <div className="chart-tooltip">-20%</div>
                  </div>
                  <div className="chart-bar" style={{height: '80%'}}>
                    <div className="chart-tooltip">-8%</div>
                  </div>
                  <div className="chart-bar" style={{height: '50%'}}>
                    <div className="chart-tooltip">-15%</div>
                  </div>
                  <div className="chart-bar active" style={{height: '30%'}}>
                    <div className="chart-tooltip">-25%</div>
                  </div>
                </div>
                <div className="dash-metrics">
                  <div className="metric-item">
                    <div className="metric-info">
                      <div className="metric-label">Carbon Offset</div>
                      <div className="metric-value">1,240 tons</div>
                    </div>
                  </div>
                  <div className="metric-item">
                    <div className="metric-info">
                      <div className="metric-label">Energy Saved</div>
                      <div className="metric-value">34% ↓</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="wave-animation"></div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="section-container">
          <h2 className="section-title">Intelligent Carbon Management</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>Real-time Monitoring</h3>
              <p>Track emissions across all operations with precision.</p>
            </div>
            <div className="feature-card">
              <h3>AI-Powered Insights</h3>
              <p>Get actionable recommendations powered by machine learning.</p>
            </div>
            <div className="feature-card">
              <h3>Advanced Analytics</h3>
              <p>Visualize trends and predict future carbon footprint.</p>
            </div>
            <div className="feature-card">
              <h3>Smart Optimization</h3>
              <p>Automated strategies to reduce emissions efficiently.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Visualization Preview Section */}
      <section className="visualization">
        <div className="viz-container">
          <div className="laptop-mockup">
            <div className="laptop-screen">
              <div className="screen-content">
                <div className="metric-box">
                  <div className="metric-label">CO₂ Emissions</div>
                  <div className="metric-value">-24%</div>
                </div>
                <div className="mini-chart"></div>
              </div>
            </div>
          </div>
          <h2 className="viz-text">See your carbon footprint come alive in real time.</h2>
        </div>
      </section>

      {/* Testimonials / Impact Section */}
      <section className="testimonials">
        <div className="section-container">
          <h2 className="section-title">Trusted by Leading Organizations</h2>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <div className="testimonial-content">
                "EcoSphere AI helped us reduce emissions by 35% in just 6 months."
              </div>
              <div className="testimonial-author">
                <div>
                  <div className="author-name">Sarah Chen</div>
                  <div className="author-role">Sustainability Director, TechCorp</div>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <div className="testimonial-content">
                "The AI predictions are incredibly accurate. A game-changer for our ESG goals."
              </div>
              <div className="testimonial-author">
                <div>
                  <div className="author-name">Michael Rodriguez</div>
                  <div className="author-role">CEO, GreenVentures</div>
                </div>
              </div>
            </div>
            <div className="testimonial-card">
              <div className="testimonial-content">
                "Real-time monitoring transformed how we approach sustainability."
              </div>
              <div className="testimonial-author">
                <div className="author-avatar">👤</div>
                <div>
                  <div className="author-name">Emma Thompson</div>
                  <div className="author-role">Operations Lead, EcoManufacture</div>
                </div>
              </div>
            </div>
          </div>
          <div className="impact-stats">
            <div className="stat">
              <div className="stat-value">1.2M</div>
              <div className="stat-label">Tons CO₂ Saved</div>
            </div>
            <div className="stat">
              <div className="stat-value">500+</div>
              <div className="stat-label">Organizations</div>
            </div>
            <div className="stat">
              <div className="stat-value">98%</div>
              <div className="stat-label">Satisfaction Rate</div>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="cta">
        <div className="cta-content">
          <h2 className="cta-title">Let's build a cleaner future — together.</h2>
          <button className="btn-cta">Get Started</button>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-links">
            <a href="#about">About</a>
            <a href="#contact">Contact</a>
            <a href="#terms">Terms</a>
            <a href="#privacy">Privacy</a>
          </div>
          <div className="footer-icons">
            <span>🌿</span>
            <span>🌍</span>
            <span>♻️</span>
          </div>
          <div className="footer-copyright">
            © 2025 CarbonEx. All rights reserved.
          </div>
        </div>
      </footer>
        </>
      )}
    </div>
  );
}

export default App;
