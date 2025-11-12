from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from openai import OpenAI

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

class LogoutRequest(BaseModel):
    token: str

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

# Chat Models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    token: str
    message: str
    conversationHistory: List[ChatMessage] = []

# Initialize NVIDIA OpenAI Client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

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
    
    # Build conversation messages
    messages = [
        {
            "role": "system",
            "content": f"""You are EcoAI, an expert sustainability and carbon management assistant for CarbonEx. 
You help organizations reduce their carbon footprint and achieve net-zero goals.

{org_context}

Your role is to:
1. Provide actionable carbon reduction recommendations
2. Analyze energy consumption patterns
3. Suggest renewable energy transitions
4. Offer industry-specific sustainability best practices
5. Help organizations meet their carbon neutrality goals

RESPONSE GUIDELINES:
- Be detailed and data-driven with specific recommendations
- When showing data comparisons, clearly list items with their attributes (e.g., "Energy Source | Percentage | Impact")
- Structure information clearly with main sections and subsections
- Include emojis for visual appeal
- Provide specific, actionable steps
- Include timelines and phases when discussing roadmaps
- Compare current state vs target state
- Prioritize recommendations (High/Medium/Low priority)
- Be conversational but professional

Focus on creating comprehensive, well-organized responses that can be easily formatted into tables and sections."""
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
    """
        }
    ]
    
    # Add conversation history (last 5 messages for context)
    for msg in request.conversationHistory[-5:]:"""
        }
    ]
- Use <p> tags for paragraphs
- Use <strong> for important text
- Use <br> for line breaks
- Add priority badges: <span class="badge badge-success">Low</span>, <span class="badge badge-warning">Medium</span>, <span class="badge badge-danger">High</span>, <span class="badge badge-info">Info</span>

EXAMPLE RESPONSE FORMAT (ALWAYS USE THIS STRUCTURE):
<div>
<h2>� Tata Steel - Company Overview</h2>
<p>Here's a comprehensive analysis of your organization's carbon footprint and path to net-zero by 2040.</p>

<h3>📊 Current Energy Mix</h3>
<table>
<thead>
<tr>
  <th>Energy Source</th>
  <th>Current %</th>
  <th>CO2 Impact</th>
  <th>Priority</th>
</tr>
</thead>
<tbody>
<tr>
  <td>⚡ Electricity</td>
  <td>40%</td>
  <td>High</td>
  <td><span class="badge badge-danger">Critical</span></td>
</tr>
<tr>
  <td>🛢️ Diesel</td>
  <td>30%</td>
  <td>Medium</td>
  <td><span class="badge badge-warning">Medium</span></td>
</tr>
<tr>
  <td>🔥 LPG</td>
  <td>20%</td>
  <td>Low</td>
  <td><span class="badge badge-success">Low</span></td>
</tr>
<tr>
  <td>🌞 Renewables</td>
  <td>10%</td>
  <td>Zero</td>
  <td><span class="badge badge-success">Excellent</span></td>
</tr>
</tbody>
</table>

<h3>🎯 Roadmap to Net-Zero by 2040</h3>
<table>
<thead>
<tr>
  <th>Phase</th>
  <th>Years</th>
  <th>Key Actions</th>
  <th>Target Reduction</th>
</tr>
</thead>
<tbody>
<tr>
  <td><strong>Phase 1</strong></td>
  <td>2025-2030</td>
  <td>
    <ul>
      <li>Install 50 MW solar capacity</li>
      <li>Electrify 30% of fleet</li>
    </ul>
  </td>
  <td>20%</td>
</tr>
<tr>
  <td><strong>Phase 2</strong></td>
  <td>2031-2035</td>
  <td>
    <ul>
      <li>Transition to green hydrogen</li>
      <li>Complete fleet electrification</li>
    </ul>
  </td>
  <td>30%</td>
</tr>
</tbody>
</table>

<h3>💡 Top 3 Recommendations</h3>
<ol>
  <li><strong>Increase renewable energy to 50%</strong> - Install on-site solar panels and sign PPAs</li>
  <li><strong>Optimize diesel usage</strong> - Implement route optimization and preventive maintenance</li>
  <li><strong>Expand carbon offset programs</strong> - Invest in verified forestry projects</li>
</ol>
</div>

REMEMBER: ALWAYS format data, comparisons, and statistics in HTML tables. Never use plain text formatting."""
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
        # STEP 1: Call NVIDIA API for content generation (plain text)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
            stream=False
        )
        
        plain_response = completion.choices[0].message.content
        print(f"Plain response received: {plain_response[:200]}...")
        
        # STEP 2: Use second LLM call to convert to HTML
        html_conversion_prompt = f"""Convert the following text into clean, well-structured HTML format.

RULES:
1. Wrap everything in a <div> tag
2. Use <h2> for main titles, <h3> for sections, <h4> for subsections
3. Convert any tabular data or comparisons into proper HTML <table> with <thead> and <tbody>
4. Use <ul> and <li> for bullet points
5. Use <ol> and <li> for numbered lists
6. Add badges for priorities: <span class="badge badge-success">text</span>, <span class="badge badge-warning">text</span>, <span class="badge badge-danger">text</span>
7. Use <strong> for emphasis
8. Add emojis in headings
9. Use <p> tags for paragraphs

TEXT TO CONVERT:
{plain_response}

Return ONLY the HTML, nothing else."""

        html_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an HTML formatting expert. Convert text to clean, semantic HTML. Always wrap content in tables when showing data comparisons or lists of items with multiple attributes."
                },
                {
                    "role": "user",
                    "content": html_conversion_prompt
                }
            ],
            temperature=0.3,
            top_p=0.9,
            max_tokens=3000,
            stream=False
        )
        
        response_text = html_completion.choices[0].message.content
        print(f"HTML response received: {response_text[:200]}...")
        
        # Ensure response is wrapped in div if not already
        if not response_text.strip().startswith('<div>'):
            response_text = f'<div>{response_text}</div>'
        
        # Basic HTML validation - if response doesn't contain any HTML tags, use plain response
        if '<table>' not in response_text and '<h2>' not in response_text:
            # Fallback: manually format the plain response
            response_text = f'<div><p>{plain_response.replace(chr(10), "</p><p>")}</p></div>'
        
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

@app.get("/")
async def root():
    return {"message": "CarbonEx Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
