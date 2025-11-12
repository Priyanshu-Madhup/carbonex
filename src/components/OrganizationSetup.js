import React, { useState, useEffect } from 'react';
import './OrganizationSetup.css';
import logoImage from '../assets/carbonex.png';

function OrganizationSetup({ onNavigateToDashboard, onNavigateToRecommendations, onNavigateToOrgSetup, onNavigateToHome, onComplete, onBack, user, onLogout }) {
  const [currentStep, setCurrentStep] = useState(0); // Start from step 0 for file upload
  const [showSuccess, setShowSuccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileError, setFileError] = useState('');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState({ step: '', percentage: 0 });
  const [successData, setSuccessData] = useState(null);
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

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file type
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    const validExtensions = ['.csv', '.xls', '.xlsx'];
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));

    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      setFileError('Please upload a valid CSV or Excel file (.csv, .xls, .xlsx)');
      setUploadedFile(null);
      return;
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setFileError('File size must be less than 10MB');
      setUploadedFile(null);
      return;
    }

    setFileError('');
    setUploadedFile(file);
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setFileError('');
  };

  const nextStep = () => {
    if (currentStep === 0 && !uploadedFile) {
      setFileError('Please upload a dataset file before proceeding');
      return;
    }
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setIsSubmitting(true);
      setSubmitProgress({ step: 'Saving organization data...', percentage: 25 });
      
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Please login first');
        setIsSubmitting(false);
        return;
      }

      // Step 1: Save organization data
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

      setSubmitProgress({ step: 'Uploading dataset...', percentage: 50 });

      // Step 2: Upload dataset file if present
      if (uploadedFile) {
        const formDataFile = new FormData();
        formDataFile.append('file', uploadedFile);

        const uploadResponse = await fetch(
          `http://localhost:8000/api/ml/upload-dataset?session_token=${token}`,
          {
            method: 'POST',
            body: formDataFile
          }
        );

        if (uploadResponse.ok) {
          console.log('Dataset uploaded successfully');
          
          setSubmitProgress({ step: 'Training ML model...', percentage: 75 });
          
          // Step 3: Auto-train model after upload
          const trainResponse = await fetch(
            `http://localhost:8000/api/ml/train-model?session_token=${token}`,
            {
              method: 'POST'
            }
          );

          if (trainResponse.ok) {
            const result = await trainResponse.json();
            console.log('Model trained successfully:', result.metrics);
            
            // Step 4: Generate AI insights from charts (this takes time)
            setSubmitProgress({ step: 'Analyzing emissions with AI...', percentage: 80 });
            
            let insightsGenerated = false;
            try {
              const insightsResponse = await fetch(
                `http://localhost:8000/api/ml/generate-insights/ORG001?session_token=${token}`,
                {
                  method: 'POST'
                }
              );

              if (insightsResponse.ok) {
                const insightsResult = await insightsResponse.json();
                console.log('✅ AI insights generated:', insightsResult.insight);
                insightsGenerated = true;
                
                // Update progress after insights are done
                setSubmitProgress({ step: 'Finalizing...', percentage: 95 });
              } else {
                const errorText = await insightsResponse.text();
                console.error('Insights generation failed:', errorText);
                alert('Model trained successfully, but AI insights generation failed. You can still use the dashboard.');
              }
            } catch (error) {
              console.error('Error generating insights:', error);
              alert('Model trained successfully, but AI insights generation failed. You can still use the dashboard.');
            }
            
            // Short delay to show final progress
            await new Promise(resolve => setTimeout(resolve, 500));
            setSubmitProgress({ step: 'Complete!', percentage: 100 });
            
            // Store success data for the success card
            setSuccessData({
              organization: {
                name: formData.organizationName,
                industry: formData.industry,
                employees: formData.numEmployees,
                location: `${formData.city}, ${formData.country}`
              },
              metrics: result.metrics,
              insightsGenerated: insightsGenerated
            });
            
            // Delay before showing success card
            setTimeout(() => {
              setIsSubmitting(false);
              setShowSuccess(true);
              setViewMode(true);
              setIsEditing(false);
            }, 800);
          } else {
            console.error('Model training failed');
            setIsSubmitting(false);
            alert('Organization saved, but model training failed. You can retry from Dashboard.');
          }
        } else {
          console.error('Dataset upload failed');
          setIsSubmitting(false);
          alert('Organization saved, but dataset upload failed. Please try again from Dashboard.');
        }
      } else {
        // No file uploaded, just save organization
        setIsSubmitting(false);
        setViewMode(true);
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Error saving organization data:', error);
      setIsSubmitting(false);
      alert('Failed to save organization data: ' + error.message);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setViewMode(false);
    setCurrentStep(0); // Start from dataset upload step
  };

  const totalEnergy = formData.electricity + formData.diesel + formData.lpg + formData.renewables;

  const getSustainabilityPractices = () => {
    const practices = [];
    if (formData.solarPanels) practices.push('Solar Panels');
    if (formData.evFleet) practices.push('EV Fleet');
    if (formData.greenProcurement) practices.push('Green Procurement');
    if (formData.carbonOffsets) practices.push('Carbon Offsets');
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
              <img src={logoImage} alt="CarbonEx" className="logo-image" />
              <span className="logo-text">CarbonEx</span>
            </div>
            <div className="nav-links">
              <a href="#dashboard" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToDashboard(); }}>
                Dashboard
              </a>
              <a href="#recommendations" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToRecommendations(); }}>
                Recommendations
              </a>
              <a href="#organization" className="nav-tab active">Organization Setup</a>
              <a href="#settings" className="nav-tab" onClick={(e) => { e.preventDefault(); }}>Settings</a>
              <a href="#help" className="nav-tab" onClick={(e) => { e.preventDefault(); }}>Help / Docs</a>
              <div className="nav-actions">
                <button className="edit-btn-nav" onClick={handleEdit}>
                  Edit
                </button>
              </div>
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

        {/* Organization Details View */}
        <div className="setup-container">
          <div className="setup-header">
            <h1 className="setup-title">Organization Profile</h1>
            <p className="setup-subtitle">
              Your complete organization details and sustainability information
            </p>
            <button 
              className="btn-quick-dashboard"
              onClick={(e) => {
                e.preventDefault();
                onNavigateToDashboard();
              }}
            >
              Go to Dashboard
            </button>
          </div>

          <div className="details-view-container">
            {/* Organization Details Section */}
            <div className="details-section">
              <h2 className="details-section-title">
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
                Operations & Energy
              </h2>
              <div className="details-grid">
                <div className="detail-item full-width">
                  <span className="detail-label">Energy Distribution</span>
                  <div className="energy-breakdown">
                    <div className="energy-item">
                      <span>Electricity:</span>
                      <span className="energy-percent">{formData.electricity}%</span>
                    </div>
                    <div className="energy-item">
                      <span>Diesel:</span>
                      <span className="energy-percent">{formData.diesel}%</span>
                    </div>
                    <div className="energy-item">
                      <span>LPG:</span>
                      <span className="energy-percent">{formData.lpg}%</span>
                    </div>
                    <div className="energy-item">
                      <span>Renewables:</span>
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
      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-container">
          <div 
            className="logo"
            onClick={(e) => {
              e.preventDefault();
              onNavigateToDashboard();
            }}
            style={{ cursor: 'pointer' }}
          >
            <span className="logo-icon">🌿</span>
            <span className="logo-text">CarbonEx</span>
          </div>
          <div className="nav-links">
            <a href="#dashboard" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToDashboard(); }}>
              Dashboard
            </a>
            <a href="#recommendations" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToRecommendations(); }}>
              Recommendations
            </a>
            <a href="#organization" className="nav-tab active">Organization Setup</a>
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

      {/* Main Form Container */}
      <div className="setup-container">
        <div className="setup-header">
          <h1 className="setup-title">Set Up Your Organization Profile</h1>
          <p className="setup-subtitle">
            Provide details below so CarbonEx can personalize your carbon tracking and forecasting dashboard.
          </p>
          <button 
            className="btn-quick-dashboard"
            onClick={(e) => {
              e.preventDefault();
              onNavigateToDashboard();
            }}
          >
            Go to Dashboard
          </button>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div className="progress-steps">
            <div className={`progress-step ${currentStep >= 0 ? 'active' : ''}`}>
              <div className="step-circle">0</div>
              <span className="step-label">Dataset</span>
            </div>
            <div className={`progress-line ${currentStep >= 1 ? 'active' : ''}`}></div>
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
          <div className="progress-text">Step {currentStep} of 4</div>
        </div>

        {/* Form Card */}
        <div className="form-card">
          <form onSubmit={handleSubmit}>
            {/* Step 0 - Dataset Upload */}
            {currentStep === 0 && (
              <div className="form-step step-0">
                <h2 className="step-title">
                  Upload Your Dataset
                </h2>
                <p className="step-description">
                  Upload your organization's carbon emission data in CSV or Excel format
                </p>

                <div className="file-upload-section">
                  <div className="file-upload-area">
                    <input
                      type="file"
                      id="dataset-file"
                      accept=".csv,.xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
                      onChange={handleFileUpload}
                      style={{ display: 'none' }}
                    />
                    <label htmlFor="dataset-file" className="file-upload-label">
                      <div className="upload-icon">📁</div>
                      <h3>Drag and drop your file here</h3>
                      <p>or click to browse</p>
                      <span className="file-formats">Supported formats: CSV, XLS, XLSX (Max 10MB)</span>
                    </label>
                  </div>

                  {fileError && (
                    <div className="file-error">
                      <span className="error-icon">⚠️</span>
                      {fileError}
                    </div>
                  )}

                  {uploadedFile && (
                    <div className="uploaded-file-info">
                      <div className="file-details">
                        <span className="file-icon">📄</span>
                        <div className="file-info">
                          <p className="file-name">{uploadedFile.name}</p>
                          <p className="file-size">
                            {(uploadedFile.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                        <button
                          type="button"
                          className="remove-file-btn"
                          onClick={handleRemoveFile}
                        >
                          ❌
                        </button>
                      </div>
                      <div className="file-success">
                        <span className="success-icon">✅</span>
                        File uploaded successfully!
                      </div>
                    </div>
                  )}

                  <div className="file-requirements">
                    <h4>📋 Dataset Requirements:</h4>
                    <ul>
                      <li>Include columns for date, emission source, and quantity</li>
                      <li>Data should be in chronological order</li>
                      <li>Use standard units (tonnes CO2e, kWh, liters, etc.)</li>
                      <li>Ensure data covers at least the past 6 months</li>
                    </ul>
                  </div>
                </div>

                <div className="form-buttons">
                  <button type="button" className="btn-next" onClick={nextStep}>
                    Next Step →
                  </button>
                </div>
              </div>
            )}

            {/* Step 1 - Organization Details */}
            {currentStep === 1 && (
              <div className="form-step step-1">
                <h2 className="step-title">
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
                  <button type="button" className="btn-prev" onClick={prevStep}>
                    ← Previous
                  </button>
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
                    Submit & Generate Dashboard
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Loading Progress Overlay */}
        {isSubmitting && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="loading-spinner"></div>
              <h3 className="loading-title">{submitProgress.step}</h3>
              <div className="progress-bar-wrapper">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${submitProgress.percentage}%` }}
                ></div>
              </div>
              <p className="loading-percentage">{submitProgress.percentage}%</p>
            </div>
          </div>
        )}

        {/* Success Card */}
        {showSuccess && successData && (
          <div className="success-overlay">
            <div className="success-card">
              <div className="success-icon-wrapper">
                <svg className="success-checkmark" viewBox="0 0 52 52">
                  <circle className="success-checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                  <path className="success-checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
              </div>
              
              <h2 className="success-title">Analysis Ready!</h2>
              <p className="success-subtitle">Your organization has been successfully configured</p>
              
              <div className="success-details">
                <div className="success-detail-group">
                  <h3 className="success-section-title">Organization Details</h3>
                  <div className="success-detail-row">
                    <span className="detail-label">Name:</span>
                    <span className="detail-value">{successData.organization.name}</span>
                  </div>
                  <div className="success-detail-row">
                    <span className="detail-label">Industry:</span>
                    <span className="detail-value">{successData.organization.industry}</span>
                  </div>
                  <div className="success-detail-row">
                    <span className="detail-label">Employees:</span>
                    <span className="detail-value">{successData.organization.employees}</span>
                  </div>
                  <div className="success-detail-row">
                    <span className="detail-label">Location:</span>
                    <span className="detail-value">{successData.organization.location}</span>
                  </div>
                </div>
                
                <div className="success-detail-group">
                  <h3 className="success-section-title">Model Performance</h3>
                  <div className="success-detail-row">
                    <span className="detail-label">R² Score:</span>
                    <span className="detail-value">{(successData.metrics.r2 * 100).toFixed(2)}%</span>
                  </div>
                  <div className="success-detail-row">
                    <span className="detail-label">Accuracy:</span>
                    <span className="detail-value">Excellent</span>
                  </div>
                  <div className="success-detail-row">
                    <span className="detail-label">Status:</span>
                    <span className="detail-value status-ready">Ready for Predictions</span>
                  </div>
                  {successData.insightsGenerated && (
                    <div className="success-detail-row">
                      <span className="detail-label">AI Insights:</span>
                      <span className="detail-value status-ready">✓ Generated</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="success-actions">
                <button 
                  className="btn-dashboard"
                  onClick={() => {
                    setShowSuccess(false);
                    onNavigateToDashboard();
                  }}
                >
                  Go to Dashboard
                </button>
                <button 
                  className="btn-close"
                  onClick={() => setShowSuccess(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default OrganizationSetup;
