import React, { useEffect, useState } from 'react';
import './App.css';
import Login from './components/Login';
import Signup from './components/Signup';

function App() {
  const [scrollY, setScrollY] = useState(0);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleSignupSuccess = (userData) => {
    setUser(userData);
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
  };

  return (
    <div className="App">
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

      {/* Floating Background Elements */}
      <div className="floating-icons">
        <span className="float-icon leaf">🌿</span>
        <span className="float-icon earth">🌍</span>
        <span className="float-icon energy">⚡</span>
        <span className="float-icon cloud">☁️</span>
        <span className="float-icon leaf2">🍃</span>
      </div>

      {/* Header / Navbar */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <span className="logo-icon">🌿</span>
            <span className="logo-text">EcoSphere AI</span>
          </div>
          <div className="nav-links">
            <a href="#home">Home</a>
            <a href="#features">Features</a>
            <a href="#dashboard">Dashboard</a>
            {user ? (
              <>
                <span className="user-name">Hi, {user.name}!</span>
                <button className="logout-btn" onClick={handleLogout}>Logout</button>
              </>
            ) : (
              <>
                <button className="login-btn" onClick={() => setShowLogin(true)}>Login</button>
                <button className="signup-btn" onClick={() => setShowSignup(true)}>Signup</button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-left">
            <h1 className="hero-title">Monitor. Predict. Reduce.</h1>
            <p className="hero-subtitle">
              Empowering organizations to achieve net-zero through AI.
            </p>
            <div className="hero-buttons">
              <button className="btn-primary">Try Demo</button>
              <button className="btn-outline">Learn More</button>
            </div>
          </div>
          <div className="hero-right">
            <div className="dashboard-illustration">
              <div className="dash-card">
                <div className="dash-header">Carbon Analytics</div>
                <div className="dash-chart">
                  <div className="chart-bar" style={{height: '60%'}}></div>
                  <div className="chart-bar" style={{height: '40%'}}></div>
                  <div className="chart-bar" style={{height: '80%'}}></div>
                  <div className="chart-bar" style={{height: '50%'}}></div>
                  <div className="chart-bar" style={{height: '30%'}}></div>
                </div>
                <div className="dash-icons">
                  <span className="dash-icon">🌳</span>
                  <span className="dash-icon">💨</span>
                  <span className="dash-icon">☀️</span>
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
              <div className="feature-icon">🌿</div>
              <h3>Real-time Monitoring</h3>
              <p>Track emissions across all operations with precision.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚙️</div>
              <h3>AI-Powered Insights</h3>
              <p>Get actionable recommendations powered by machine learning.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Advanced Analytics</h3>
              <p>Visualize trends and predict future carbon footprint.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💡</div>
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
                <div className="author-avatar">👤</div>
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
                <div className="author-avatar">👤</div>
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
            © 2025 EcoSphere AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
