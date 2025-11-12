import React, { useState, useEffect } from 'react';
import './Dashboard.css';

function Dashboard({ user, sessionToken, onNavigateToDashboard, onNavigateToRecommendations, onNavigateToOrgSetup, onNavigateToHome, onBack, onLogout }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // Fetch model info, historical data, and auto-generate forecast on component mount
  useEffect(() => {
    fetchModelInfo();
    fetchHistoricalData();
    autoGenerateForecast();
  }, []);

  const fetchModelInfo = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/ml/model-info?session_token=${sessionToken}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setModelInfo(data);
      }
    } catch (error) {
      console.error('Error fetching model info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHistoricalData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/ml/historical-data/ORG001?session_token=${sessionToken}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setHistoricalData(data);
      } else {
        console.log('Historical data not available yet');
      }
    } catch (error) {
      console.log('Historical data not available:', error);
    }
  };

  const autoGenerateForecast = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Use ORG001 as default organization
      const response = await fetch(
        `http://localhost:8000/api/ml/forecast/ORG001?session_token=${sessionToken}`
      );

      if (response.ok) {
        const data = await response.json();
        setForecastData(data);
      } else {
        // Silently fail if model not trained yet
        console.log('Forecast not available yet');
      }
    } catch (error) {
      console.log('Forecast not available:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = () => {
    if (!forecastData || !forecastData.predictions) return null;

    const predictions = forecastData.predictions.map(p => p.predicted_emissions);
    const totalPredicted = predictions.reduce((sum, val) => sum + val, 0);
    const avgWeekly = totalPredicted / predictions.length;
    const maxWeek = Math.max(...predictions);
    const minWeek = Math.min(...predictions);

    return {
      totalPredicted: totalPredicted.toFixed(2),
      avgWeekly: avgWeekly.toFixed(2),
      maxWeek: maxWeek.toFixed(2),
      minWeek: minWeek.toFixed(2)
    };
  };

  const stats = calculateStats();

  // Close dropdown when clicking outside
  useEffect(() => {
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

  return (
    <div className="dashboard">
      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-container">
          <div 
            className="logo"
            onClick={(e) => {
              e.preventDefault();
              onNavigateToHome();
            }}
            style={{ cursor: 'pointer' }}
          >
            <span className="logo-icon">🌿</span>
            <span className="logo-text">CarbonEx</span>
          </div>
          <div className="nav-links">
            <a href="#dashboard" className="nav-tab active">Dashboard</a>
            <a href="#recommendations" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToRecommendations(); }}>
              Recommendations
            </a>
            <a href="#organization" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToOrgSetup(); }}>
              Organization Setup
            </a>
            <a href="#settings" className="nav-tab" onClick={(e) => { e.preventDefault(); }}>Settings</a>
            <a href="#help" className="nav-tab" onClick={(e) => { e.preventDefault(); }}>Help / Docs</a>
            <div className="profile-dropdown">
              <span 
                className="user-icon" 
                title={user?.name || 'User'}
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              >
                👤
              </span>
              {showProfileDropdown && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <div className="dropdown-user-name">{user?.name || 'User'}</div>
                    <div className="dropdown-user-email">{user?.email || 'user@example.com'}</div>
                  </div>
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item" onClick={onLogout}>
                    <span className="dropdown-icon">🚪</span>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>Carbon Emissions Dashboard</h1>
          <p className="subtitle">AI-powered insights and 52-week forecast analysis</p>
        </div>

      {error && (
        <div className="error-banner">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Dataset Not Available - Show Message */}
      {!modelInfo?.dataset_exists && !isLoading && (
        <div className="dashboard-section">
          <div className="info-message-box">
            <div className="info-icon-large">📊</div>
            <h2>Get Started with Your Carbon Analytics</h2>
            <p>Upload your emission dataset to unlock powerful insights and predictions.</p>
            <div className="info-steps">
              <div className="info-step">
                <span className="step-number">1</span>
                <span>Go to <strong>Organization Setup</strong></span>
              </div>
              <div className="info-step">
                <span className="step-number">2</span>
                <span>Upload your emissions dataset</span>
              </div>
              <div className="info-step">
                <span className="step-number">3</span>
                <span>Complete the setup to enable forecasting</span>
              </div>
              <div className="info-step">
                <span className="step-number">4</span>
                <span>Return here to view analytics and forecasts</span>
              </div>
            </div>
            <button 
              onClick={() => onNavigateToOrgSetup()} 
              className="btn-primary"
              style={{ marginTop: '2rem' }}
            >
              Go to Organization Setup
            </button>
          </div>
        </div>
      )}

      {/* Forecast Results Section - Auto-loaded */}
      {forecastData && stats && (
        <div className="dashboard-section results-section">
          <h2>Emission Analysis & Forecast</h2>
          
          {/* Historical Data Chart */}
          {historicalData && historicalData.historical_data && (
            <div className="chart-container">
              <h3>Historical Emissions Data (Uploaded Dataset)</h3>
              <div className="chart-with-axis">
                <div className="y-axis">
                  {(() => {
                    const maxValue = Math.max(...historicalData.historical_data.map(r => r.total_emissions));
                    const step = maxValue / 5;
                    return [5, 4, 3, 2, 1, 0].map((i) => (
                      <div key={i} className="y-axis-label">
                        {(step * i).toFixed(0)}
                      </div>
                    ));
                  })()}
                </div>
                <div className="simple-chart">
                  {historicalData.historical_data.map((record, idx) => {
                    const maxValue = Math.max(...historicalData.historical_data.map(r => r.total_emissions));
                    const barHeight = (record.total_emissions / maxValue) * 100;
                    
                    return (
                      <div key={idx} className="chart-bar-wrapper" title={`Week ${record.week}: ${record.total_emissions.toFixed(2)} tCO₂e`}>
                        <div
                          className="chart-bar historical-bar"
                          style={{ height: `${barHeight}%` }}
                        >
                          {idx % 4 === 0 && <span className="bar-label">W{record.week}</span>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="chart-axis">
                <span>Week 1</span>
                <span>Week 13</span>
                <span>Week 26</span>
                <span>Week 39</span>
                <span>Week 52</span>
              </div>
            </div>
          )}
          
          {/* Statistics Cards */}
          <div className="stats-grid">
            <div className="stat-card total-card">
              <div className="stat-content">
                <h3>Total Predicted (52 weeks)</h3>
                <p className="stat-value">{stats.totalPredicted} <span className="unit">tCO₂e</span></p>
              </div>
            </div>

            <div className="stat-card average-card">
              <div className="stat-content">
                <h3>Average Weekly</h3>
                <p className="stat-value">{stats.avgWeekly} <span className="unit">tCO₂e</span></p>
              </div>
            </div>

            <div className="stat-card high-card">
              <div className="stat-content">
                <h3>Highest Week</h3>
                <p className="stat-value">{stats.maxWeek} <span className="unit">tCO₂e</span></p>
              </div>
            </div>

            <div className="stat-card low-card">
              <div className="stat-content">
                <h3>Lowest Week</h3>
                <p className="stat-value">{stats.minWeek} <span className="unit">tCO₂e</span></p>
              </div>
            </div>
          </div>

          {/* Simple Chart Visualization */}
          <div className="chart-container">
            <h3>52-Week Emission Forecast</h3>
            <div className="chart-with-axis">
              <div className="y-axis">
                {(() => {
                  const maxValue = Math.max(...forecastData.predictions.map(p => p.predicted_emissions));
                  const step = maxValue / 5;
                  return [5, 4, 3, 2, 1, 0].map((i) => (
                    <div key={i} className="y-axis-label">
                      {(step * i).toFixed(0)}
                    </div>
                  ));
                })()}
              </div>
              <div className="simple-chart">
                {forecastData.predictions.map((pred, idx) => {
                  const maxValue = Math.max(...forecastData.predictions.map(p => p.predicted_emissions));
                  const barHeight = (pred.predicted_emissions / maxValue) * 100;
                  
                  return (
                    <div key={idx} className="chart-bar-wrapper" title={`Week ${pred.week}: ${pred.predicted_emissions.toFixed(2)} tCO₂e`}>
                      <div
                        className="chart-bar"
                        style={{ height: `${barHeight}%` }}
                      >
                        {idx % 4 === 0 && <span className="bar-label">W{pred.week}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="chart-axis">
              <span>Week 1</span>
              <span>Week 13</span>
              <span>Week 26</span>
              <span>Week 39</span>
              <span>Week 52</span>
            </div>
          </div>

          {/* Data Table */}
          <div className="data-table-container">
            <h3>Detailed Predictions</h3>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Week</th>
                    <th>Date</th>
                    <th>Predicted Emissions (tCO₂e)</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastData.predictions.map((pred, idx) => (
                    <tr key={idx}>
                      <td>Week {pred.week}</td>
                      <td>{pred.date}</td>
                      <td className="emission-value">{pred.predicted_emissions.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Historical Comparison */}
          {forecastData.historical && forecastData.historical.length > 0 && (
            <div className="comparison-section">
              <h3>Historical vs Predicted Comparison</h3>
              <div className="comparison-stats">
                <div className="comparison-card">
                  <h4>Historical Average (Last 52 weeks)</h4>
                  <p className="comparison-value">
                    {(forecastData.historical.reduce((sum, h) => sum + h.actual_emissions, 0) / 
                      forecastData.historical.length).toFixed(2)} tCO₂e/week
                  </p>
                </div>
                <div className="comparison-card">
                  <h4>Predicted Average (Next 52 weeks)</h4>
                  <p className="comparison-value">{stats.avgWeekly} tCO₂e/week</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State - Model not trained */}
      {!forecastData && !isLoading && modelInfo?.dataset_exists && !modelInfo?.model_exists && (
        <div className="empty-state">
          <h3>Setting Up Your Analytics</h3>
          <p>Your dataset is ready. We're preparing your personalized carbon emission forecasts.</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="dashboard-section">
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <h3>Loading Your Carbon Analytics...</h3>
            <p>Preparing insights and forecast data</p>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

export default Dashboard;
