from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

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

@app.get("/")
async def root():
    return {"message": "CarbonEx Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
