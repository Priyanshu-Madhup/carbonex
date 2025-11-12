from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from groq import Groq
import os
from dotenv import load_dotenv
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
from io import BytesIO

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware to allow React frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE = "users.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            organization_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            num_employees INTEGER NOT NULL,
            electricity INTEGER NOT NULL,
            diesel INTEGER NOT NULL,
            lpg INTEGER NOT NULL,
            renewables INTEGER NOT NULL,
            num_vehicles INTEGER,
            fuel_usage INTEGER,
            country TEXT NOT NULL,
            city TEXT NOT NULL,
            goal_year INTEGER NOT NULL,
            reduction_goal INTEGER NOT NULL,
            solar_panels BOOLEAN DEFAULT 0,
            ev_fleet BOOLEAN DEFAULT 0,
            green_procurement BOOLEAN DEFAULT 0,
            carbon_offsets BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emission_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id TEXT NOT NULL,
            insight_text TEXT NOT NULL,
            chart_image_base64 TEXT,
            historical_mean REAL,
            historical_std REAL,
            forecast_mean REAL,
            forecast_std REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    token: str

class OrganizationSetup(BaseModel):
    organizationName: str
    industry: str
    numEmployees: int
    electricity: int
    diesel: int
    lpg: int
    renewables: int
    numVehicles: int = 0
    fuelUsage: int = 0
    country: str
    city: str
    goalYear: int
    reductionGoal: int
    solarPanels: bool = False
    evFleet: bool = False
    greenProcurement: bool = False
    carbonOffsets: bool = False

class LogoutRequest(BaseModel):
    token: str

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    token: str
    message: str
    conversationHistory: List[ChatMessage] = []

# Initialize Groq Client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def create_session(user_id: int) -> str:
    conn = get_db()
    cursor = conn.cursor()
    token = generate_token()
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    conn.commit()
    conn.close()
    return token

def verify_token(token: str) -> Optional[int]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
        (token, datetime.now())
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def generate_emission_charts(organization_id: str) -> Dict[str, str]:
    """
    Generate matplotlib charts for historical and forecast data
    Returns base64 encoded images
    """
    try:
        backend_dir = Path(__file__).parent
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        model_path = backend_dir / "xgboost_emission_model.pkl"
        
        # Read historical data
        df = pd.read_csv(csv_path)
        org_data = df[df['organization_id'] == organization_id].copy()
        org_data['week_start_date'] = pd.to_datetime(org_data['week_start_date'], format='%d-%m-%Y', dayfirst=True)
        org_data = org_data.sort_values('week_start_date')
        last_52_weeks = org_data.tail(52)
        
        # Get forecast data
        from train_xgboost_model import EmissionForecaster
        forecaster = EmissionForecaster.load(str(model_path))
        forecast_df = forecaster.predict_52_weeks(str(csv_path), organization_id)
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('#f8fafc')
        
        # Historical Chart
        weeks_hist = [f"W{i+1}" for i in range(len(last_52_weeks))]
        emissions_hist = last_52_weeks['total_emissions_tco2e'].values
        
        ax1.bar(weeks_hist, emissions_hist, color='#00bfa6', alpha=0.8, edgecolor='#008577', linewidth=1.5)
        ax1.set_title('Historical Emissions Data (Last 52 Weeks)', fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('Week', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Emissions (tCO₂e)', fontsize=12, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_facecolor('#ffffff')
        
        # Add statistics text
        stats_text = f"Mean: {emissions_hist.mean():.2f} | Std: {emissions_hist.std():.2f} | Min: {emissions_hist.min():.2f} | Max: {emissions_hist.max():.2f} tCO₂e"
        ax1.text(0.5, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Set x-axis ticks to show every 4th week
        tick_positions = list(range(0, len(weeks_hist), 4))
        ax1.set_xticks(tick_positions)
        ax1.set_xticklabels([weeks_hist[i] for i in tick_positions], rotation=45)
        
        # Forecast Chart
        weeks_forecast = [f"W{i+1}" for i in range(len(forecast_df))]
        emissions_forecast = [p['predicted_emissions'] for p in forecast_df]
        
        ax2.bar(weeks_forecast, emissions_forecast, color='#667eea', alpha=0.8, edgecolor='#4c51bf', linewidth=1.5)
        ax2.set_title('52-Week Emission Forecast (ML Prediction)', fontsize=16, fontweight='bold', pad=20)
        ax2.set_xlabel('Week', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Predicted Emissions (tCO₂e)', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        ax2.set_facecolor('#ffffff')
        
        # Add forecast statistics
        forecast_mean = np.mean(emissions_forecast)
        forecast_std = np.std(emissions_forecast)
        forecast_min = np.min(emissions_forecast)
        forecast_max = np.max(emissions_forecast)
        forecast_stats = f"Mean: {forecast_mean:.2f} | Std: {forecast_std:.2f} | Min: {forecast_min:.2f} | Max: {forecast_max:.2f} tCO₂e"
        ax2.text(0.5, 0.98, forecast_stats, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Set x-axis ticks to show every 4th week
        ax2.set_xticks(tick_positions)
        ax2.set_xticklabels([weeks_forecast[i] for i in tick_positions], rotation=45)
        
        plt.tight_layout()
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return {
            "image_base64": image_base64,
            "historical_stats": {
                "mean": float(emissions_hist.mean()),
                "std": float(emissions_hist.std()),
                "min": float(emissions_hist.min()),
                "max": float(emissions_hist.max())
            },
            "forecast_stats": {
                "mean": float(forecast_mean),
                "std": float(forecast_std),
                "min": float(forecast_min),
                "max": float(forecast_max)
            }
        }
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        import traceback
        traceback.print_exc()
        raise


def analyze_charts_with_ai(image_base64: str, historical_stats: dict, forecast_stats: dict) -> str:
    """
    Use Groq Vision API to analyze emission charts and generate insights
    Returns concise 2-3 line insight
    """
    try:
        # Create data URL for the image
        image_url = f"data:image/png;base64,{image_base64}"
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze these carbon emission charts and provide a concise 2-3 line insight.

Historical Stats: Mean={historical_stats['mean']:.2f}, Std={historical_stats['std']:.2f}, Min={historical_stats['min']:.2f}, Max={historical_stats['max']:.2f} tCO₂e
Forecast Stats: Mean={forecast_stats['mean']:.2f}, Std={forecast_stats['std']:.2f}, Min={forecast_stats['min']:.2f}, Max={forecast_stats['max']:.2f} tCO₂e

Focus on:
1. Key trend differences between historical and forecast
2. Any concerning patterns or positive changes
3. Actionable insight for emissions reduction

Keep response to 2-3 sentences maximum."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_completion_tokens=200,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        insight = completion.choices[0].message.content.strip()
        return insight
        
    except Exception as e:
        print(f"Error analyzing charts with AI: {e}")
        import traceback
        traceback.print_exc()
        return "Unable to generate AI insights at this time."


# API endpoints
@app.post("/api/signup", response_model=UserResponse)
async def signup(user: UserSignup):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (user.name, user.email, hashed_password)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    # Create session
    token = create_session(user_id)
    
    return UserResponse(
        id=user_id,
        name=user.name,
        email=user.email,
        token=token
    )

@app.post("/api/login", response_model=UserResponse)
async def login(user: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    # Find user
    hashed_password = hash_password(user.password)
    cursor.execute(
        "SELECT id, name, email FROM users WHERE email = ? AND password = ?",
        (user.email, hashed_password)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    token = create_session(result[0])
    
    return UserResponse(
        id=result[0],
        name=result[1],
        email=result[2],
        token=token
    )

@app.get("/api/verify")
async def verify(token: str):
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": result[0],
        "name": result[1],
        "email": result[2]
    }

@app.post("/api/logout")
async def logout(request: LogoutRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (request.token,))
    conn.commit()
    conn.close()
    return {"message": "Logged out successfully"}

@app.post("/api/organization/setup")
async def setup_organization(org: OrganizationSetup, token: str):
    # Verify token and get user_id
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if organization already exists for this user
    cursor.execute("SELECT id FROM organizations WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing organization
        cursor.execute("""
            UPDATE organizations SET
                organization_name = ?,
                industry = ?,
                num_employees = ?,
                electricity = ?,
                diesel = ?,
                lpg = ?,
                renewables = ?,
                num_vehicles = ?,
                fuel_usage = ?,
                country = ?,
                city = ?,
                goal_year = ?,
                reduction_goal = ?,
                solar_panels = ?,
                ev_fleet = ?,
                green_procurement = ?,
                carbon_offsets = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            org.organizationName, org.industry, org.numEmployees,
            org.electricity, org.diesel, org.lpg, org.renewables,
            org.numVehicles, org.fuelUsage, org.country, org.city,
            org.goalYear, org.reductionGoal,
            org.solarPanels, org.evFleet, org.greenProcurement, org.carbonOffsets,
            user_id
        ))
    else:
        # Insert new organization
        cursor.execute("""
            INSERT INTO organizations (
                user_id, organization_name, industry, num_employees,
                electricity, diesel, lpg, renewables, num_vehicles, fuel_usage,
                country, city, goal_year, reduction_goal,
                solar_panels, ev_fleet, green_procurement, carbon_offsets
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, org.organizationName, org.industry, org.numEmployees,
            org.electricity, org.diesel, org.lpg, org.renewables,
            org.numVehicles, org.fuelUsage, org.country, org.city,
            org.goalYear, org.reductionGoal,
            org.solarPanels, org.evFleet, org.greenProcurement, org.carbonOffsets
        ))
    
    conn.commit()
    conn.close()
    
    return {"message": "Organization setup saved successfully"}

@app.get("/api/organization")
async def get_organization(token: str):
    # Verify token and get user_id
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            organization_name, industry, num_employees,
            electricity, diesel, lpg, renewables, num_vehicles, fuel_usage,
            country, city, goal_year, reduction_goal,
            solar_panels, ev_fleet, green_procurement, carbon_offsets,
            created_at, updated_at
        FROM organizations WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "organizationName": result[0],
        "industry": result[1],
        "numEmployees": result[2],
        "electricity": result[3],
        "diesel": result[4],
        "lpg": result[5],
        "renewables": result[6],
        "numVehicles": result[7],
        "fuelUsage": result[8],
        "country": result[9],
        "city": result[10],
        "goalYear": result[11],
        "reductionGoal": result[12],
        "solarPanels": bool(result[13]),
        "evFleet": bool(result[14]),
        "greenProcurement": bool(result[15]),
        "carbonOffsets": bool(result[16]),
        "createdAt": result[17],
        "updatedAt": result[18]
    }

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    # Verify token and get user_id
    user_id = verify_token(request.token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get organization data
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            organization_name, industry, num_employees,
            electricity, diesel, lpg, renewables, num_vehicles, fuel_usage,
            country, city, goal_year, reduction_goal,
            solar_panels, ev_fleet, green_procurement, carbon_offsets
        FROM organizations WHERE user_id = ?
    """, (user_id,))
    org_result = cursor.fetchone()
    
    # Get AI insights for the organization (using ORG001 as default)
    cursor.execute("""
        SELECT insight_text, historical_mean, forecast_mean
        FROM emission_insights
        WHERE organization_id = 'ORG001'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    insight_result = cursor.fetchone()
    conn.close()
    
    # Build context about the organization
    org_context = ""
    if org_result:
        org_context = f"""
Organization Data Context:
- Name: {org_result[0]}
- Industry: {org_result[1]}
- Number of Employees: {org_result[2]}
- Energy Mix: Electricity {org_result[3]}%, Diesel {org_result[4]}%, LPG {org_result[5]}%, Renewables {org_result[6]}%
- Fleet: {org_result[7]} vehicles, Fuel Usage: {org_result[8]} liters/month
- Location: {org_result[10]}, {org_result[9]}
- Carbon Neutrality Goal: {org_result[11]}
- Reduction Target: {org_result[12]}%
- Current Sustainability Practices:
  * Solar Panels: {'Yes' if org_result[13] else 'No'}
  * EV Fleet: {'Yes' if org_result[14] else 'No'}
  * Green Procurement: {'Yes' if org_result[15] else 'No'}
  * Carbon Offsets: {'Yes' if org_result[16] else 'No'}
"""
    
    # Add AI-generated insights to context
    insights_context = ""
    if insight_result:
        insights_context = f"""

📊 AI-POWERED EMISSION ANALYSIS:
{insight_result[0]}

Historical Average: {insight_result[1]:.2f} tCO₂e | Forecast Average: {insight_result[2]:.2f} tCO₂e

Use these data-driven insights when providing recommendations and answering questions about emission patterns.
"""
    
    # Build conversation messages with HTML formatting instructions
    messages = [
        {
            "role": "system",
            "content": f"""You are EcoAI, an expert sustainability and carbon management assistant for CarbonEx. 
You help organizations reduce their carbon footprint and achieve net-zero goals.

{org_context}
{insights_context}

Your role is to:
1. Provide actionable carbon reduction recommendations
2. Analyze energy consumption patterns
3. Suggest renewable energy transitions
4. Offer industry-specific sustainability best practices
5. Help organizations meet their carbon neutrality goals

CRITICAL - RESPONSE FORMATTING RULES:
You MUST format your entire response in clean HTML. Follow these rules strictly:

1. Wrap everything in a <div> tag
2. Use <h2> for main titles, <h3> for sections, <h4> for subsections
3. For ANY data, comparisons, or structured information, use HTML tables:
   <table>
     <thead><tr><th>Column 1</th><th>Column 2</th></tr></thead>
     <tbody><tr><td>Data 1</td><td>Data 2</td></tr></tbody>
   </table>
4. Use <ul> and <li> for bullet points
5. Use <ol> and <li> for numbered lists
6. Use <p> tags for paragraphs
7. Use <strong> for emphasis
8. DO NOT use any emojis anywhere in your response - keep all text clean and professional
9. Use plain text headings without any icons or decorative characters

EXAMPLE RESPONSE FORMAT:
<div>
<h2>Your Carbon Roadmap</h2>
<p>Here's your personalized plan based on your data.</p>

<h3>Current Energy Mix</h3>
<table>
<thead><tr><th>Energy Source</th><th>Percentage</th><th>Impact</th></tr></thead>
<tbody>
<tr><td>Electricity</td><td>40%</td><td>High</td></tr>
<tr><td>Renewables</td><td>20%</td><td>Low</td></tr>
</tbody>
</table>

<h3>Recommendations</h3>
<ul>
<li><strong>Phase 1:</strong> Increase renewable energy to 40%</li>
<li><strong>Phase 2:</strong> Implement energy efficiency audits</li>
</ul>
</div>

Always return valid HTML without emojis. Be detailed and provide specific recommendations."""
        }
    ]
    
    # Add conversation history (last 5 messages for context)
    for msg in request.conversationHistory[-5:]:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": request.message
    })
    
    try:
        # Call Groq API with HTML formatting in system prompt
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
            stream=False
        )
        
        response_text = completion.choices[0].message.content
        print(f"[LLM] Response received (length: {len(response_text)})")
        print(f"[LLM] First 300 chars: {response_text[:300]}")
        
        return {
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error calling NVIDIA API: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response with HTML formatting
        renewable_pct = org_result[6] if org_result else 0
        fallback_html = f"""<div>
<h2>⚠️ Temporary Connection Issue</h2>
<p>I apologize, but I'm having trouble connecting to my AI knowledge base right now.</p>

<h3>🌱 Quick Recommendations Based on Your Profile:</h3>
<ul>
  <li><strong>Increase Renewable Energy:</strong> Focus on boosting from {renewable_pct}% to at least 30% in the next phase</li>
  <li><strong>Energy Efficiency Audits:</strong> Consider comprehensive audits for all facilities</li>
  <li><strong>Fleet Electrification:</strong> Explore electric vehicle options for your fleet</li>
  <li><strong>Green Procurement:</strong> Prioritize suppliers with strong sustainability credentials</li>
</ul>

<p><em>Please try again in a moment for more detailed, personalized recommendations.</em> 🔄</p>
</div>"""
        
        return {
            "response": fallback_html,
            "timestamp": datetime.now().isoformat()
        }

# ==================== ML FORECASTING ENDPOINTS ====================

@app.post("/api/ml/upload-dataset")
async def upload_dataset(
    file: UploadFile = File(...),
    session_token: str = None
):
    """
    Upload CSV dataset for training
    Saves to backend/ecosphere_synthetic.csv
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Save uploaded file
        backend_dir = Path(__file__).parent
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        
        with open(csv_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Dataset uploaded successfully",
            "filepath": str(csv_path),
            "filename": file.filename,
            "size_bytes": csv_path.stat().st_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading dataset: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/ml/train-model")
async def train_model(session_token: str = None):
    """
    Train XGBoost model on uploaded dataset
    Returns training metrics
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Import forecaster
        from train_xgboost_model import EmissionForecaster
        
        backend_dir = Path(__file__).parent
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        model_path = backend_dir / "xgboost_emission_model.pkl"
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found. Please upload CSV first.")
        
        # Train model
        forecaster = EmissionForecaster()
        metrics = forecaster.train(str(csv_path))
        
        # Save model
        forecaster.save(str(model_path))
        
        return {
            "message": "Model trained successfully",
            "metrics": metrics,
            "model_path": str(model_path),
            "training_date": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error training model: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.get("/api/ml/forecast/{organization_id}")
async def get_forecast(organization_id: str, session_token: str = None):
    """
    Get 52-week emission forecast for organization
    Returns predicted emissions for next year
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Load model
        from train_xgboost_model import EmissionForecaster
        
        backend_dir = Path(__file__).parent
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        model_path = backend_dir / "xgboost_emission_model.pkl"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="Model not found. Please train model first.")
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found.")
        
        # Load forecaster
        forecaster = EmissionForecaster.load(str(model_path))
        
        # Get predictions
        predictions = forecaster.predict_52_weeks(str(csv_path), organization_id)
        
        # Get historical data for comparison
        historical = forecaster.get_current_emissions(str(csv_path), organization_id, weeks=52)
        
        return {
            "organization_id": organization_id,
            "forecast_weeks": 52,
            "predictions": predictions,
            "historical": historical,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating forecast: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@app.get("/api/ml/model-info")
async def get_model_info(session_token: str = None):
    """
    Get information about the trained model
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        backend_dir = Path(__file__).parent
        model_path = backend_dir / "xgboost_emission_model.pkl"
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        
        if not model_path.exists():
            return {
                "model_exists": False,
                "dataset_exists": csv_path.exists(),
                "message": "No trained model found"
            }
        
        # Load model info
        import joblib
        artifact = joblib.load(str(model_path))
        
        return {
            "model_exists": True,
            "dataset_exists": csv_path.exists(),
            "training_date": artifact.get('training_date'),
            "num_features": len(artifact.get('feature_columns', [])),
            "model_type": "XGBoost Regressor",
            "model_path": str(model_path)
        }
        
    except Exception as e:
        print(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.get("/api/ml/historical-data/{organization_id}")
async def get_historical_data(organization_id: str, session_token: str = None):
    """
    Get historical emission data from the uploaded dataset
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        backend_dir = Path(__file__).parent
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Read the CSV file
        import pandas as pd
        df = pd.read_csv(str(csv_path))
        
        # Filter for the specific organization
        org_data = df[df['organization_id'] == organization_id].copy()
        
        if org_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for organization {organization_id}")
        
        # Sort by date
        org_data['week_start_date'] = pd.to_datetime(org_data['week_start_date'], format='%d-%m-%Y', dayfirst=True)
        org_data = org_data.sort_values('week_start_date')
        
        # Get the last 52 weeks of historical data (or all if less than 52)
        last_52_weeks = org_data.tail(52)
        
        # Prepare response
        historical_records = []
        for idx, row in last_52_weeks.iterrows():
            historical_records.append({
                "week": len(historical_records) + 1,
                "date": row['week_start_date'].strftime('%Y-%m-%d'),
                "total_emissions": float(row['total_emissions_tco2e'])
            })
        
        return {
            "organization_id": organization_id,
            "total_records": len(historical_records),
            "historical_data": historical_records
        }
        
    except Exception as e:
        print(f"Error getting historical data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")


@app.post("/api/ml/generate-insights/{organization_id}")
async def generate_insights(organization_id: str, session_token: str = None):
    """
    Generate AI insights from emission charts using Groq Vision API
    Should be called after model training
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        if not session:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Generate charts
        print(f"Generating charts for {organization_id}...")
        chart_data = generate_emission_charts(organization_id)
        
        # Analyze with AI
        print(f"Analyzing charts with AI...")
        insight = analyze_charts_with_ai(
            chart_data['image_base64'],
            chart_data['historical_stats'],
            chart_data['forecast_stats']
        )
        
        # Store in database
        cursor.execute("""
            INSERT INTO emission_insights 
            (organization_id, insight_text, chart_image_base64, 
             historical_mean, historical_std, forecast_mean, forecast_std)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            organization_id,
            insight,
            chart_data['image_base64'],
            chart_data['historical_stats']['mean'],
            chart_data['historical_stats']['std'],
            chart_data['forecast_stats']['mean'],
            chart_data['forecast_stats']['std']
        ))
        conn.commit()
        conn.close()
        
        print(f"Insights generated successfully: {insight}")
        
        return {
            "message": "Insights generated successfully",
            "organization_id": organization_id,
            "insight": insight,
            "historical_stats": chart_data['historical_stats'],
            "forecast_stats": chart_data['forecast_stats']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@app.get("/api/ml/insights/{organization_id}")
async def get_insights(organization_id: str, session_token: str = None):
    """
    Retrieve stored AI insights for organization
    """
    try:
        # Verify session
        if not session_token:
            raise HTTPException(status_code=401, detail="Session token required")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?",
            (session_token, datetime.now())
        )
        session = cursor.fetchone()
        if not session:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Get latest insight
        cursor.execute("""
            SELECT insight_text, historical_mean, historical_std, 
                   forecast_mean, forecast_std, created_at
            FROM emission_insights
            WHERE organization_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (organization_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {
                "organization_id": organization_id,
                "insight": None,
                "message": "No insights available. Please generate insights first."
            }
        
        return {
            "organization_id": organization_id,
            "insight": result[0],
            "historical_stats": {
                "mean": result[1],
                "std": result[2]
            },
            "forecast_stats": {
                "mean": result[3],
                "std": result[4]
            },
            "generated_at": result[5]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

# ==================== END ML ENDPOINTS ====================

@app.get("/")
async def root():
    return {"message": "CarbonEx Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
