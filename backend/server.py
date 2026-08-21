from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class DocketUpdate(BaseModel):
    status: str

SEED_DOCKET = [
    {"id": "cor-1048", "priority": "urgent", "type": "Notice of delay", "subject": "Potential delay to West Quay piling works", "sender": "Marlowe Civil Engineering", "project": "West Quay Redevelopment", "received": "Today, 08:42", "deadline": "Reply by 14 Jun", "risk": "High", "risk_detail": "Notice alleges access constraints caused by the client and reserves entitlement to 18 days extension of time.", "excerpt": "We hereby notify the Employer of a delay event under clause 8.4...", "attachment": "Delay Notice 18.pdf", "status": "Needs review"},
    {"id": "cor-1047", "priority": "high", "type": "Payment claim", "subject": "Interim payment application #07", "sender": "Northstar MEP Ltd", "project": "Harbour Point Offices", "received": "Yesterday, 16:20", "deadline": "Assess by 17 Jun", "risk": "Medium", "risk_detail": "Application includes £42,600 in variation work not yet supported by an approved instruction.", "excerpt": "The Subcontractor applies for payment of the sum of £284,160...", "attachment": "Payment App 07.xlsx", "status": "Waiting on QS"},
    {"id": "cor-1045", "priority": "normal", "type": "RFI", "subject": "RFI 224: façade bracket tolerance", "sender": "Apex Facades", "project": "West Quay Redevelopment", "received": "12 Jun, 11:05", "deadline": "Reply by 19 Jun", "risk": "Low", "risk_detail": "Design clarification requested; no immediate contractual exposure identified.", "excerpt": "Please confirm whether the tolerance shown on drawing A-501 is to be maintained...", "attachment": "RFI-224.pdf", "status": "Open"},
    {"id": "cor-1041", "priority": "normal", "type": "Minutes", "subject": "Commercial meeting minutes — week 23", "sender": "Turner Project Controls", "project": "Riverside Logistics Hub", "received": "11 Jun, 14:33", "deadline": "Review by 18 Jun", "risk": "Low", "risk_detail": "Minutes contain two action owners requiring internal confirmation.", "excerpt": "Action 04: Employer to confirm the revised access sequence by Friday...", "attachment": "Commercial Minutes W23.docx", "status": "Needs review"},
]

@api_router.get("/dashboard")
async def get_dashboard():
    return {"project": {"name": "West Quay Redevelopment", "code": "WQ-042", "status": "Live", "contract": "NEC4 ECC Option C", "contract_updated": "12 Jun 2025"}, "stats": {"needs_review": 12, "urgent": 3, "waiting": 5, "open_projects": 8}, "docket": SEED_DOCKET, "insight": {"title": "Three items need attention this week", "body": "The docket has identified a delay notice and two payment claims that could affect the June forecast if left unanswered.", "items": ["Reply to Marlowe’s delay notice by 14 Jun", "Confirm instruction status for Northstar’s variation", "Approve RFI 224 response with Design"]}}

@api_router.patch("/docket/{item_id}")
async def update_docket(item_id: str, update: DocketUpdate):
    for item in SEED_DOCKET:
        if item["id"] == item_id:
            item["status"] = update.status
            return item
    raise HTTPException(status_code=404, detail="Correspondence not found")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()