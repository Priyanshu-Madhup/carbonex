import React, { useState, useEffect, useRef } from 'react';
import './Recommendations.css';
import logoImage from '../assets/carbonex.png';

function Recommendations({ user, onNavigateToDashboard, onNavigateToRecommendations, onNavigateToOrgSetup, onNavigateToHome, onBack, onLogout }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `<div>
        <h2>Welcome to EcoAI!</h2>
        <p>I'm your sustainability assistant with access to your organization's carbon footprint data.</p>
        <h3>How I Can Help:</h3>
        <ul>
          <li><strong>Carbon reduction strategies</strong> - Personalized recommendations based on your data</li>
          <li><strong>Energy efficiency insights</strong> - Optimize your energy consumption</li>
          <li><strong>Sustainability best practices</strong> - Industry-specific guidance</li>
          <li><strong>Custom analysis</strong> - Data-driven insights for your goals</li>
        </ul>
        <p>Ask me anything about reducing your carbon footprint!</p>
      </div>`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [orgData, setOrgData] = useState(null);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load organization data
    loadOrganizationData();
  }, []);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const loadOrganizationData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`http://localhost:8000/api/organization?token=${token}`);
      if (response.ok) {
        const data = await response.json();
        setOrgData(data);
      }
    } catch (error) {
      console.error('Error loading organization data:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

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

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      console.log('Sending message to API...', input.trim());
      console.log('Conversation history being sent:', updatedMessages.slice(-10));
      
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          message: input.trim(),
          conversationHistory: updatedMessages.slice(-10) // Send last 10 messages including current user message
        })
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Received response:', data);
        console.log('Response content length:', data.response?.length);
        console.log('Response content:', data.response);
        
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        };
        console.log('Assistant message created:', assistantMessage);
        setMessages([...updatedMessages, assistantMessage]);
        console.log('Messages updated with assistant response');
      } else {
        const errorData = await response.text();
        console.error('Error response:', errorData);
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages([...updatedMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuery = (query) => {
    setInput(query);
  };

  const quickQueries = [
    "What are my top carbon emission sources?",
    "How can I reduce electricity consumption?",
    "Suggest renewable energy options for my industry",
    "What sustainability practices should I prioritize?",
    "Compare my emissions to industry benchmarks"
  ];

  const formatTimestamp = (date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="recommendations-page">
      {/* Background decorations */}
      <div className="bg-decorations">
      </div>

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
            <a href="#recommendations" className="nav-tab active">Recommendations</a>
            <a href="#organization" className="nav-tab" onClick={(e) => { e.preventDefault(); onNavigateToOrgSetup(); }}>
              Organization Setup
            </a>
            <a 
              href="https://github.com/Priyanshu-Madhup/carbonex" 
              className="nav-tab" 
              target="_blank" 
              rel="noopener noreferrer"
              title="View documentation and source code"
            >
              Help / Docs
            </a>
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

      {/* Main Content */}
      <div className="recommendations-container">
        <div className="recommendations-header">
          <div className="header-content">
            <div className="ai-badge">
              <span className="ai-icon">🤖</span>
              <span className="ai-label">EcoAI Assistant</span>
            </div>
            <h1 className="recommendations-title">AI-Powered Recommendations</h1>
            <p className="recommendations-subtitle">
              Get personalized sustainability insights based on your organization's data
            </p>
          </div>
        </div>

        <div className="chat-layout">
          {/* Quick Queries Sidebar */}
          <div className="quick-queries-panel">
            <h3 className="panel-title">Quick Questions</h3>
            <div className="quick-queries-list">
              {quickQueries.map((query, index) => (
                <button
                  key={index}
                  className="quick-query-btn"
                  onClick={() => handleQuickQuery(query)}
                  disabled={loading}
                >
                  <span className="query-icon">→</span>
                  {query}
                </button>
              ))}
            </div>

            {orgData && (
              <div className="org-context-info">
                <h4 className="context-title">Your Data Context</h4>
                <div className="context-item">
                  <span className="context-label">Organization:</span>
                  <span className="context-value">{orgData.organizationName}</span>
                </div>
                <div className="context-item">
                  <span className="context-label">Industry:</span>
                  <span className="context-value">{orgData.industry}</span>
                </div>
                <div className="context-item">
                  <span className="context-label">Employees:</span>
                  <span className="context-value">{orgData.numEmployees}</span>
                </div>
                <div className="context-item">
                  <span className="context-label">Target Year:</span>
                  <span className="context-value">{orgData.goalYear}</span>
                </div>
              </div>
            )}
          </div>

          {/* Chat Area */}
          <div className="chat-area">
            <div className="messages-container">
              {messages.map((message, index) => {
                if (message.role === 'assistant') {
                  console.log(`[RENDER] Message ${index} content length:`, message.content?.length);
                  console.log(`[RENDER] Message ${index} content preview:`, message.content?.substring(0, 100));
                }
                return (
                <div
                  key={index}
                  className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <div className="message-avatar">
                    {message.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-content">
                    <div className="message-text">
                      {message.role === 'user' ? (
                        message.content
                      ) : (
                        <div dangerouslySetInnerHTML={{ __html: message.content }} />
                      )}
                    </div>
                    <div className="message-timestamp">
                      {formatTimestamp(message.timestamp)}
                    </div>
                  </div>
                </div>
              )})}
              {loading && (
                <div className="message assistant-message">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form className="chat-input-area" onSubmit={handleSendMessage}>
              <input
                type="text"
                className="chat-input"
                placeholder="Ask EcoAI anything about your sustainability goals..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={loading || !input.trim()}
              >
                <span className="send-icon">📤</span>
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
