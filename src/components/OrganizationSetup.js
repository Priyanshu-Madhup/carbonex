import React, { useState, useEffect } from 'react';
import './OrganizationSetup.css';

function OrganizationSetup({ onComplete, onBack }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [showSuccess, setShowSuccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    // Step 1
    organizationName: '',
    industry: '',
    numEmployees: '',
    // Step 2
    electricity: 40,
    diesel: 30,
    lpg: 20,
    renewables: 10,
    numVehicles: '',
    fuelUsage: '',
    country: '',
    city: '',
    // Step 3
    goalYear: '',
    reductionGoal: '',
    solarPanels: false,
    evFleet: false,
    greenProcurement: false,
    carbonOffsets: false,
  });

  useEffect(() => {
    // Load existing organization data if available
    const loadOrganizationData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await fetch(`http://localhost:8000/api/organization?token=${token}`);
        
        if (response.ok) {
          const data = await response.json();
          setFormData({
            organizationName: data.organizationName || '',
            industry: data.industry || '',
            numEmployees: data.numEmployees || '',
            electricity: data.electricity || 40,
            diesel: data.diesel || 30,
            lpg: data.lpg || 20,
            renewables: data.renewables || 10,
            numVehicles: data.numVehicles || '',
            fuelUsage: data.fuelUsage || '',
            country: data.country || '',
            city: data.city || '',
            goalYear: data.goalYear || '',
            reductionGoal: data.reductionGoal || '',
            solarPanels: data.solarPanels || false,
            evFleet: data.evFleet || false,
            greenProcurement: data.greenProcurement || false,
            carbonOffsets: data.carbonOffsets || false,
          });
          setViewMode(true); // Show data in view mode if it exists
        }
      } catch (error) {
        console.error('Error loading organization data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadOrganizationData();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSliderChange = (name, value) => {
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Please login first');
        return;
      }

      const response = await fetch(`http://localhost:8000/api/organization/setup?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save organization data');
      }

      // Switch to view mode
      setViewMode(true);
      setIsEditing(false);
      setShowSuccess(false);
    } catch (error) {
      console.error('Error saving organization data:', error);
      alert('Failed to save organization data: ' + error.message);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setViewMode(false);
    setCurrentStep(1);
  };

  const totalEnergy = formData.electricity + formData.diesel + formData.lpg + formData.renewables;

  const getSustainabilityPractices = () => {
    const practices = [];
    if (formData.solarPanels) practices.push('☀️ Solar Panels');
    if (formData.evFleet) practices.push('🚗 EV Fleet');
    if (formData.greenProcurement) practices.push('♻️ Green Procurement');
    if (formData.carbonOffsets) practices.push('🌳 Carbon Offsets');
    return practices.length > 0 ? practices.join(', ') : 'None selected';
  };

  if (loading) {
    return (
      <div className="org-setup-page">
        <div className="success-container">
          <div className="success-animation">
            <div className="success-icon">⏳</div>
          </div>
          <h1 className="success-title">Loading...</h1>
          <p className="success-message">Please wait while we load your data.</p>
        </div>
      </div>
    );
  }

  // View Mode - Display organization details
  if (viewMode) {
    return (
      <div className="org-setup-page">
        {/* Background decorations */}
        <div className="bg-decorations">
          <span className="bg-icon leaf1">🌿</span>
          <span className="bg-icon leaf2">🍃</span>
          <span className="bg-icon globe">🌍</span>
          <span className="bg-icon energy">⚡</span>
        </div>

        {/* Top Navigation */}
        <div className="setup-nav">
          <div className="nav-content">
            <div className="logo">
              <span className="logo-icon">🌿</span>
              <span className="logo-text">CarbonEx</span>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button className="edit-btn" onClick={handleEdit}>
                ✏️ Edit Details
              </button>
              <button className="back-link" onClick={onBack}>
                ← Back to Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Organization Details View */}
        <div className="setup-container">
          <div className="setup-header">
            <h1 className="setup-title">Organization Profile</h1>
            <p className="setup-subtitle">
              Your complete organization details and sustainability information
            </p>
          </div>

          <div className="details-view-container">
            {/* Organization Details Section */}
            <div className="details-section">
              <h2 className="details-section-title">
                <span className="details-emoji">🏢</span>
                Organization Details
              </h2>
              <div className="details-grid">
                <div className="detail-item">
                  <span className="detail-label">Organization Name</span>
                  <span className="detail-value">{formData.organizationName}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Industry</span>
                  <span className="detail-value">{formData.industry}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Number of Employees</span>
                  <span className="detail-value">{formData.numEmployees}</span>
                </div>
              </div>
            </div>

            {/* Operations & Energy Section */}
            <div className="details-section">
              <h2 className="details-section-title">
                <span className="details-emoji">⚡</span>
                Operations & Energy
              </h2>
              <div className="details-grid">
                <div className="detail-item full-width">
                  <span className="detail-label">Energy Distribution</span>
                  <div className="energy-breakdown">
                    <div className="energy-item">
                      <span>🔌 Electricity:</span>
                      <span className="energy-percent">{formData.electricity}%</span>
                    </div>
                    <div className="energy-item">
                      <span>🛢️ Diesel:</span>
                      <span className="energy-percent">{formData.diesel}%</span>
                    </div>
                    <div className="energy-item">
                      <span>🔥 LPG:</span>
                      <span className="energy-percent">{formData.lpg}%</span>
                    </div>
                    <div className="energy-item">
                      <span>🌞 Renewables:</span>
                      <span className="energy-percent">{formData.renewables}%</span>
                    </div>
                  </div>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Number of Vehicles</span>
                  <span className="detail-value">{formData.numVehicles || 'Not specified'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Avg. Monthly Fuel Usage</span>
                  <span className="detail-value">{formData.fuelUsage ? `${formData.fuelUsage} liters` : 'Not specified'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Country</span>
                  <span className="detail-value">{formData.country}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">City</span>
                  <span className="detail-value">{formData.city}</span>
                </div>
              </div>
            </div>

            {/* Targets & Sustainability Section */}
            <div className="details-section">
              <h2 className="details-section-title">
                <span className="details-emoji">🎯</span>
                Targets & Sustainability
              </h2>
              <div className="details-grid">
                <div className="detail-item">
                  <span className="detail-label">Carbon Neutrality Goal Year</span>
                  <span className="detail-value">{formData.goalYear}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">CO₂e Reduction Goal</span>
                  <span className="detail-value">{formData.reductionGoal}%</span>
                </div>
                <div className="detail-item full-width">
                  <span className="detail-label">Current Sustainability Practices</span>
                  <span className="detail-value practices">{getSustainabilityPractices()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showSuccess) {
    return (
      <div className="org-setup-page">
        <div className="success-container">
          <div className="success-animation">
            <div className="success-icon">✅</div>
            <div className="growing-leaf">🌱</div>
          </div>
          <h1 className="success-title">Profile Created Successfully!</h1>
          <p className="success-message">
            CarbonEx has generated a custom baseline for your organization.
          </p>
          <div className="success-summary">
            <h3>Organization Summary</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Organization:</span>
                <span className="summary-value">{formData.organizationName}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Industry:</span>
                <span className="summary-value">{formData.industry}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Employees:</span>
                <span className="summary-value">{formData.numEmployees}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Goal Year:</span>
                <span className="summary-value">{formData.goalYear}</span>
              </div>
            </div>
          </div>
          <button className="btn-dashboard" onClick={onComplete}>
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="org-setup-page">
      {/* Background decorations */}
      <div className="bg-decorations">
        <span className="bg-icon leaf1">🌿</span>
        <span className="bg-icon leaf2">🍃</span>
        <span className="bg-icon globe">🌍</span>
        <span className="bg-icon energy">⚡</span>
      </div>

      {/* Top Navigation */}
      <div className="setup-nav">
        <div className="nav-content">
          <div className="logo">
            <span className="logo-icon">🌿</span>
            <span className="logo-text">CarbonEx</span>
          </div>
          <button className="back-link" onClick={onBack}>
            ← Back to Dashboard
          </button>
        </div>
      </div>

      {/* Main Form Container */}
      <div className="setup-container">
        <div className="setup-header">
          <h1 className="setup-title">Set Up Your Organization Profile</h1>
          <p className="setup-subtitle">
            Provide details below so CarbonEx can personalize your carbon tracking and forecasting dashboard.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div className="progress-steps">
            <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>
              <div className="step-circle">1</div>
              <span className="step-label">Organization</span>
            </div>
            <div className={`progress-line ${currentStep >= 2 ? 'active' : ''}`}></div>
            <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>
              <div className="step-circle">2</div>
              <span className="step-label">Operations</span>
            </div>
            <div className={`progress-line ${currentStep >= 3 ? 'active' : ''}`}></div>
            <div className={`progress-step ${currentStep >= 3 ? 'active' : ''}`}>
              <div className="step-circle">3</div>
              <span className="step-label">Targets</span>
            </div>
          </div>
          <div className="progress-text">Step {currentStep} of 3</div>
        </div>

        {/* Form Card */}
        <div className="form-card">
          <form onSubmit={handleSubmit}>
            {/* Step 1 - Organization Details */}
            {currentStep === 1 && (
              <div className="form-step step-1">
                <h2 className="step-title">
                  <span className="step-emoji">🏢</span>
                  Organization Details
                </h2>
                <p className="step-description">Tell us about your organization</p>

                <div className="form-group">
                  <label>Organization Name</label>
                  <input
                    type="text"
                    name="organizationName"
                    value={formData.organizationName}
                    onChange={handleChange}
                    placeholder="e.g., Green Tech Solutions"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Industry</label>
                  <select
                    name="industry"
                    value={formData.industry}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Select your industry</option>
                    <option value="Manufacturing">Manufacturing</option>
                    <option value="IT">IT / Technology</option>
                    <option value="Logistics">Logistics / Transportation</option>
                    <option value="Education">Education</option>
                    <option value="Government">Government</option>
                    <option value="Retail">Retail</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Number of Employees</label>
                  <input
                    type="number"
                    name="numEmployees"
                    value={formData.numEmployees}
                    onChange={handleChange}
                    placeholder="e.g., 250"
                    min="1"
                    required
                  />
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-next" onClick={nextStep}>
                    Next →
                  </button>
                </div>
              </div>
            )}

            {/* Step 2 - Operations & Energy */}
            {currentStep === 2 && (
              <div className="form-step step-2">
                <h2 className="step-title">
                  <span className="step-emoji">⚡</span>
                  Operations & Energy
                </h2>
                <p className="step-description">Help us understand your energy consumption</p>

                <div className="form-group">
                  <label>
                    Energy Sources Distribution (Total: {totalEnergy}%)
                    <span className="tooltip">ℹ️
                      <span className="tooltip-text">Adjust sliders to match your energy mix</span>
                    </span>
                  </label>
                  
                  <div className="energy-sliders">
                    <div className="slider-group">
                      <div className="slider-label">
                        <span>🔌 Electricity</span>
                        <span className="slider-value">{formData.electricity}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formData.electricity}
                        onChange={(e) => handleSliderChange('electricity', parseInt(e.target.value))}
                        className="energy-slider"
                      />
                    </div>

                    <div className="slider-group">
                      <div className="slider-label">
                        <span>🛢️ Diesel</span>
                        <span className="slider-value">{formData.diesel}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formData.diesel}
                        onChange={(e) => handleSliderChange('diesel', parseInt(e.target.value))}
                        className="energy-slider"
                      />
                    </div>

                    <div className="slider-group">
                      <div className="slider-label">
                        <span>🔥 LPG</span>
                        <span className="slider-value">{formData.lpg}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formData.lpg}
                        onChange={(e) => handleSliderChange('lpg', parseInt(e.target.value))}
                        className="energy-slider"
                      />
                    </div>

                    <div className="slider-group">
                      <div className="slider-label">
                        <span>🌞 Renewables</span>
                        <span className="slider-value">{formData.renewables}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formData.renewables}
                        onChange={(e) => handleSliderChange('renewables', parseInt(e.target.value))}
                        className="energy-slider"
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3 className="section-title">Fleet Information</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>
                        Number of Vehicles
                        <span className="tooltip">ℹ️
                          <span className="tooltip-text">Company-owned vehicles</span>
                        </span>
                      </label>
                      <input
                        type="number"
                        name="numVehicles"
                        value={formData.numVehicles}
                        onChange={handleChange}
                        placeholder="e.g., 15"
                        min="0"
                      />
                    </div>

                    <div className="form-group">
                      <label>
                        Avg. Monthly Fuel Usage (liters)
                        <span className="tooltip">ℹ️
                          <span className="tooltip-text">Total fuel consumption per month</span>
                        </span>
                      </label>
                      <input
                        type="number"
                        name="fuelUsage"
                        value={formData.fuelUsage}
                        onChange={handleChange}
                        placeholder="e.g., 2500"
                        min="0"
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3 className="section-title">Location</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Country</label>
                      <select
                        name="country"
                        value={formData.country}
                        onChange={handleChange}
                        required
                      >
                        <option value="">Select country</option>
                        <option value="USA">United States</option>
                        <option value="UK">United Kingdom</option>
                        <option value="India">India</option>
                        <option value="Germany">Germany</option>
                        <option value="Canada">Canada</option>
                        <option value="Australia">Australia</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>City</label>
                      <input
                        type="text"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        placeholder="e.g., San Francisco"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-back" onClick={prevStep}>
                    ← Back
                  </button>
                  <button type="button" className="btn-next" onClick={nextStep}>
                    Next →
                  </button>
                </div>
              </div>
            )}

            {/* Step 3 - Targets & Sustainability */}
            {currentStep === 3 && (
              <div className="form-step step-3">
                <h2 className="step-title">
                  <span className="step-emoji">🎯</span>
                  Targets & Sustainability
                </h2>
                <p className="step-description">Set your sustainability goals and initiatives</p>

                <div className="form-row">
                  <div className="form-group">
                    <label>Carbon Neutrality Goal Year</label>
                    <input
                      type="number"
                      name="goalYear"
                      value={formData.goalYear}
                      onChange={handleChange}
                      placeholder="e.g., 2030"
                      min="2025"
                      max="2050"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>CO₂e Reduction Goal (%)</label>
                    <input
                      type="number"
                      name="reductionGoal"
                      value={formData.reductionGoal}
                      onChange={handleChange}
                      placeholder="e.g., 50"
                      min="0"
                      max="100"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Current Sustainability Practices</label>
                  <p className="form-hint">Select all that apply to your current initiatives</p>
                  
                  <div className="checkbox-grid">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        name="solarPanels"
                        checked={formData.solarPanels}
                        onChange={handleChange}
                      />
                      <span className="checkbox-custom"></span>
                      <span className="checkbox-text">
                        <span className="checkbox-icon">☀️</span>
                        Solar Panels
                      </span>
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        name="evFleet"
                        checked={formData.evFleet}
                        onChange={handleChange}
                      />
                      <span className="checkbox-custom"></span>
                      <span className="checkbox-text">
                        <span className="checkbox-icon">🚗</span>
                        EV Fleet
                      </span>
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        name="greenProcurement"
                        checked={formData.greenProcurement}
                        onChange={handleChange}
                      />
                      <span className="checkbox-custom"></span>
                      <span className="checkbox-text">
                        <span className="checkbox-icon">♻️</span>
                        Green Procurement
                      </span>
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        name="carbonOffsets"
                        checked={formData.carbonOffsets}
                        onChange={handleChange}
                      />
                      <span className="checkbox-custom"></span>
                      <span className="checkbox-text">
                        <span className="checkbox-icon">🌳</span>
                        Carbon Offsets
                      </span>
                    </label>
                  </div>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-back" onClick={prevStep}>
                    ← Back
                  </button>
                  <button type="submit" className="btn-submit">
                    Submit & Generate Dashboard ✨
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}

export default OrganizationSetup;
