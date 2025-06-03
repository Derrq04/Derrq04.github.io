from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt

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

# Security
security = HTTPBearer()
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    user_type: str  # "customer" or "seller"
    phone: Optional[str] = None
    location: Optional[str] = None
    business_name: Optional[str] = None  # for sellers
    business_description: Optional[str] = None  # for sellers
    is_verified: bool = False
    subscription_status: str = "trial"  # "trial", "active", "expired"
    trial_expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    user_type: str
    phone: Optional[str] = None
    location: Optional[str] = None
    business_name: Optional[str] = None
    business_description: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Request(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    title: str
    description: str
    budget_min: float
    budget_max: float
    categories: List[str]
    location: Optional[str] = None
    timeline: Optional[str] = None
    images: List[str] = []
    quantity: int = 1
    status: str = "open"  # "open", "offer_accepted", "completed", "cancelled"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RequestCreate(BaseModel):
    title: str
    description: str
    budget_min: float
    budget_max: float
    categories: List[str]
    location: Optional[str] = None
    timeline: Optional[str] = None
    images: List[str] = []
    quantity: int = 1

class Offer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    seller_id: str
    price: float
    description: str
    delivery_details: str
    images: List[str] = []
    terms: Optional[str] = None
    status: str = "pending"  # "pending", "accepted", "declined"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OfferCreate(BaseModel):
    request_id: str
    price: float
    description: str
    delivery_details: str
    images: List[str] = []
    terms: Optional[str] = None

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    offer_id: Optional[str] = None
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    request_id: str
    offer_id: Optional[str] = None
    receiver_id: str
    content: str

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Authentication Routes
@api_router.post("/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    del user_dict["password"]
    user = User(**user_dict)
    
    # Store user with hashed password
    user_doc = user.dict()
    user_doc["password"] = hashed_password
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.dict()
    }

@api_router.post("/login")
async def login(login_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc["id"]})
    
    # Remove password from response
    del user_doc["password"]
    user = User(**user_doc)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.dict()
    }

@api_router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

# Request Routes
@api_router.post("/requests", response_model=Request)
async def create_request(request_data: RequestCreate, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "customer":
        raise HTTPException(status_code=403, detail="Only customers can create requests")
    
    request_dict = request_data.dict()
    request_dict["customer_id"] = current_user.id
    request_obj = Request(**request_dict)
    
    await db.requests.insert_one(request_obj.dict())
    return request_obj

@api_router.get("/requests", response_model=List[Request])
async def get_requests(
    category: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Build filter
    filter_dict = {"status": "open"}
    
    if category:
        filter_dict["categories"] = {"$in": [category]}
    
    if min_budget is not None:
        filter_dict["budget_max"] = {"$gte": min_budget}
    
    if max_budget is not None:
        filter_dict["budget_min"] = {"$lte": max_budget}
    
    if location:
        filter_dict["location"] = {"$regex": location, "$options": "i"}
    
    requests = await db.requests.find(filter_dict).sort("created_at", -1).to_list(100)
    return [Request(**req) for req in requests]

@api_router.get("/requests/my")
async def get_my_requests(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "customer":
        raise HTTPException(status_code=403, detail="Only customers can view their requests")
    
    requests = await db.requests.find({"customer_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [Request(**req) for req in requests]

@api_router.get("/requests/{request_id}")
async def get_request(request_id: str, current_user: User = Depends(get_current_user)):
    request_doc = await db.requests.find_one({"id": request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return Request(**request_doc)

# Offer Routes
@api_router.post("/offers", response_model=Offer)
async def create_offer(offer_data: OfferCreate, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can create offers")
    
    # Check if request exists
    request_doc = await db.requests.find_one({"id": offer_data.request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check if seller already has an offer for this request
    existing_offer = await db.offers.find_one({
        "request_id": offer_data.request_id,
        "seller_id": current_user.id
    })
    if existing_offer:
        raise HTTPException(status_code=400, detail="You already have an offer for this request")
    
    offer_dict = offer_data.dict()
    offer_dict["seller_id"] = current_user.id
    offer_obj = Offer(**offer_dict)
    
    await db.offers.insert_one(offer_obj.dict())
    return offer_obj

@api_router.get("/offers/request/{request_id}")
async def get_offers_for_request(request_id: str, current_user: User = Depends(get_current_user)):
    # Check if request exists and user has access
    request_doc = await db.requests.find_one({"id": request_id})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Only request owner can see all offers
    if current_user.user_type == "customer" and request_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    offers = await db.offers.find({"request_id": request_id}).sort("created_at", -1).to_list(100)
    
    # Populate seller details
    for offer in offers:
        seller = await db.users.find_one({"id": offer["seller_id"]})
        if seller:
            offer["seller_name"] = seller.get("business_name") or seller.get("full_name")
            offer["seller_location"] = seller.get("location")
    
    return [Offer(**offer) for offer in offers]

@api_router.get("/offers/my")
async def get_my_offers(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view their offers")
    
    offers = await db.offers.find({"seller_id": current_user.id}).sort("created_at", -1).to_list(100)
    
    # Populate request details
    for offer in offers:
        request_doc = await db.requests.find_one({"id": offer["request_id"]})
        if request_doc:
            offer["request_title"] = request_doc["title"]
            offer["request_budget"] = f"KES {request_doc['budget_min']}-{request_doc['budget_max']}"
    
    return [Offer(**offer) for offer in offers]

@api_router.put("/offers/{offer_id}/accept")
async def accept_offer(offer_id: str, current_user: User = Depends(get_current_user)):
    # Find offer
    offer_doc = await db.offers.find_one({"id": offer_id})
    if not offer_doc:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Find request
    request_doc = await db.requests.find_one({"id": offer_doc["request_id"]})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check if user is the request owner
    if current_user.user_type != "customer" or request_doc["customer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only request owner can accept offers")
    
    # Update offer status
    await db.offers.update_one({"id": offer_id}, {"$set": {"status": "accepted"}})
    
    # Update request status
    await db.requests.update_one({"id": offer_doc["request_id"]}, {"$set": {"status": "offer_accepted"}})
    
    # Decline all other offers for this request
    await db.offers.update_many(
        {"request_id": offer_doc["request_id"], "id": {"$ne": offer_id}},
        {"$set": {"status": "declined"}}
    )
    
    return {"message": "Offer accepted successfully"}

# Messaging Routes
@api_router.post("/messages", response_model=Message)
async def send_message(message_data: MessageCreate, current_user: User = Depends(get_current_user)):
    message_dict = message_data.dict()
    message_dict["sender_id"] = current_user.id
    message_obj = Message(**message_dict)
    
    await db.messages.insert_one(message_obj.dict())
    return message_obj

@api_router.get("/messages/conversation/{request_id}")
async def get_conversation(
    request_id: str,
    other_user_id: str,
    current_user: User = Depends(get_current_user)
):
    messages = await db.messages.find({
        "request_id": request_id,
        "$or": [
            {"sender_id": current_user.id, "receiver_id": other_user_id},
            {"sender_id": other_user_id, "receiver_id": current_user.id}
        ]
    }).sort("created_at", 1).to_list(100)
    
    return [Message(**msg) for msg in messages]

# Dashboard data
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.user_type == "customer":
        # Customer stats
        total_requests = await db.requests.count_documents({"customer_id": current_user.id})
        active_requests = await db.requests.count_documents({"customer_id": current_user.id, "status": "open"})
        total_offers = await db.offers.count_documents({
            "request_id": {"$in": [req["id"] for req in await db.requests.find({"customer_id": current_user.id}).to_list(1000)]}
        })
        
        return {
            "total_requests": total_requests,
            "active_requests": active_requests,
            "total_offers_received": total_offers
        }
    
    elif current_user.user_type == "seller":
        # Seller stats
        total_offers = await db.offers.count_documents({"seller_id": current_user.id})
        accepted_offers = await db.offers.count_documents({"seller_id": current_user.id, "status": "accepted"})
        pending_offers = await db.offers.count_documents({"seller_id": current_user.id, "status": "pending"})
        
        return {
            "total_offers": total_offers,
            "accepted_offers": accepted_offers,
            "pending_offers": pending_offers
        }

# Categories endpoint
@api_router.get("/categories")
async def get_categories():
    return [
        "Apparel & Fashion",
        "Electronics & Gadgets", 
        "Home & Garden",
        "Automotive",
        "Services",
        "Books & Media",
        "Custom Items",
        "Food & Beverages",
        "Health & Beauty",
        "Sports & Recreation"
    ]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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
