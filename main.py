"""
FastAPI app for AXA ADAPT.

Receives room images, runs YOLOv8 detection, and returns structured fall hazards
with risk assessment based on user profile.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

import cv2
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from ultralytics import YOLO
from apscheduler.schedulers.background import BackgroundScheduler

# Import improved core logic
from axa_app_mvp.logic.hazard_scoring import (
    load_risk_matrix,
    load_thresholds,
    load_detection_mapping,
    map_detected_objects_to_hazards,
    score_hazards
)
from axa_app_mvp.logic.qr_utils import (
    generate_secure_url,
    create_qr_code,
    validate_token,
    cleanup_expired_tokens,
    TokenExpiredError,
    TokenValidationError,
    QRCodeError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
PROFILES_DIR = BASE_DIR / "axa_app_mvp" / "profiles"
MODEL_PATH = BASE_DIR / "models" / "yolov8n.pt"  # Update with your model path

# Ensure required directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
PROFILES_DIR.mkdir(exist_ok=True, parents=True)

# Initialize FastAPI app
app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="axa_app_mvp/templates")

# Allow all origins for now (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="axa_app_mvp/static"), name="static")
app.mount("/static/images", StaticFiles(directory="axa_app_mvp/static/images"), name="images")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Load YOLO model (lazy load on first request)
model = None
def get_model():
    global model
    if model is None:
        try:
            model = YOLO(str(MODEL_PATH))
            logger.info(f"Loaded YOLO model from {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to load object detection model"
            )
    return model

# Pydantic models for request/response validation
class UserProfile(BaseModel):
    id: str
    name: str
    mobility: bool = False
    vision: bool = False
    cognition: bool = False
    age: Optional[int] = None
    conditions: List[str] = []

class HazardDetectionRequest(BaseModel):
    profile: UserProfile
    room_images: List[Dict[str, str]]  # List of dicts with 'room' and 'image_url' or 'image_base64'

class QRGenerateRequest(BaseModel):
    user_id: str
    access_type: str = "medical_summary"
    expiry_hours: int = 24
    metadata: Optional[Dict] = None

# Helper functions
def load_user_profile(user_id: str) -> Dict:
    """Load user profile from file."""
    profile_path = PROFILES_DIR / f"health_profile_{user_id}.json"
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Profile not found for user {user_id}")
        # Return a default profile for demo purposes
        return {
            "id": user_id,
            "name": "Demo User",
            "mobility": False,
            "vision": False,
            "cognition": False,
            "age": 65,
            "conditions": []
        }
    except json.JSONDecodeError:
        logger.error(f"Invalid profile JSON for user {user_id}")
        raise HTTPException(status_code=500, detail="Invalid profile data")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Serve the home page.
    """
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/assess", response_class=HTMLResponse)
async def start_assessment(request: Request):
    """
    Serve the assessment start page.
    """
    return templates.TemplateResponse("room_scan_upload.html", {"request": request})

@app.get("/qr", response_class=HTMLResponse)
async def qr_tools(request: Request):
    """
    Serve the QR tools page.
    """
    return templates.TemplateResponse("qr_card_generator.html", {"request": request})

@app.get("/qr-tool/start", response_class=HTMLResponse)
async def qr_tool_start(request: Request):
    """
    Start the QR code creation process.
    """
    return templates.TemplateResponse("qr_tool_start.html", {"request": request})

@app.post("/qr-tool/content")
async def qr_tool_content(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    conditions: List[str] = Form([]),
    medications: str = Form(""),
    allergies: str = Form(""),
    emergency_contact: str = Form(...),
    emergency_phone: str = Form(...),
    relationship: str = Form(...)
):
    """
    Process the profile form and show the content selection screen.
    """
    # In a real app, you would validate the form data here
    # and possibly save it to a database or session
    
    # For now, we'll just pass the form data to the template
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "conditions": conditions,
        "medications": medications,
        "allergies": allergies,
        "emergency_contact": emergency_contact,
        "emergency_phone": emergency_phone,
        "relationship": relationship,
        # Calculate age from date of birth for display
        "age": (datetime.now().date() - datetime.strptime(date_of_birth, "%Y-%m-%d").date()).days // 365
    }
    
    return templates.TemplateResponse(
        "qr_tool_content.html",
        {"request": request, "form_data": form_data}
    )

@app.post("/qr-tool/privacy")
async def qr_tool_privacy(
    request: Request,
    # Profile data
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    conditions: List[str] = Form([]),
    medications: str = Form(""),
    allergies: str = Form(""),
    emergency_contact: str = Form(...),
    emergency_phone: str = Form(...),
    relationship: str = Form(...),
    # Content selection
    include_medical: bool = Form(False),
    include_medications: bool = Form(False),
    include_allergies: bool = Form(False),
    include_emergency: bool = Form(False)
):
    """
    Process the content selection and show the privacy settings screen.
    """
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "conditions": conditions,
        "medications": medications,
        "allergies": allergies,
        "emergency_contact": emergency_contact,
        "emergency_phone": emergency_phone,
        "relationship": relationship,
        "include_medical": include_medical,
        "include_medications": include_medications,
        "include_allergies": include_allergies,
        "include_emergency": include_emergency
    }
    
    return templates.TemplateResponse(
        "qr_tool_privacy.html",
        {"request": request, "form_data": form_data, "today": datetime.now().strftime("%Y-%m-%d")}
    )

@app.post("/qr-tool/generate")
async def qr_tool_generate(
    request: Request,
    # Profile data
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: str = Form(...),
    conditions: List[str] = Form([]),
    medications: str = Form(""),
    allergies: str = Form(""),
    emergency_contact: str = Form(...),
    emergency_phone: str = Form(...),
    relationship: str = Form(...),
    # Content selection
    include_medical: bool = Form(False),
    include_medications: bool = Form(False),
    include_allergies: bool = Form(False),
    include_emergency: bool = Form(False),
    # Privacy settings
    privacy: str = Form(...),
    expiry: str = Form("24"),
    custom_expiry_date: Optional[str] = Form(None)
):
    """
    Generate the QR code and show the final screen.
    """
    # Process expiry
    expiry_date = None
    if privacy == "private":
        if expiry == "custom" and custom_expiry_date:
            expiry_date = datetime.strptime(custom_expiry_date, "%Y-%m-%d").date()
        else:
            hours = int(expiry) if expiry.isdigit() else 24
            expiry_date = datetime.utcnow() + timedelta(hours=hours)
    
    # Generate a unique ID for this QR code
    qr_id = str(uuid.uuid4())
    
    # Prepare the data to be stored
    qr_data = {
        "id": qr_id,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expiry_date.isoformat() if expiry_date else None,
        "privacy": privacy,
        "profile": {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "conditions": conditions,
            "medications": medications,
            "allergies": allergies,
            "emergency_contact": emergency_contact,
            "emergency_phone": emergency_phone,
            "relationship": relationship
        },
        "content": {
            "include_medical": include_medical,
            "include_medications": include_medical and include_medications,
            "include_allergies": include_medical and include_allergies,
            "include_emergency": include_emergency
        },
        "access_count": 0
    }
    
    # Save the QR data (in a real app, you'd save this to a database)
    qr_file = save_qr_data(qr_id, qr_data)
    
    # Generate the QR code URL
    qr_url = generate_qr_code_url(qr_data)
    
    # In a real app, you would generate an actual QR code image here
    # For now, we'll use a placeholder
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_url}"
    
    # Generate an access code for private QR codes
    access_code = None
    if privacy == "private":
        access_code = str(uuid.uuid4())[:8].upper()
    
    # Format the expiry date for display
    display_expiry = None
    if expiry_date:
        display_expiry = expiry_date.strftime("%B %d, %Y at %H:%M")
    
    return templates.TemplateResponse(
        "qr_tool_generate.html",
        {
            "request": request,
            "qr_code_url": qr_code_url,
            "qr_url": qr_url,
            "privacy": privacy,
            "access_code": access_code,
            "expiry_date": display_expiry,
            "created_date": datetime.now().strftime("%B %d, %Y at %H:%M")
        }
    )

@app.get("/qr-tools")
async def qr_tools(request: Request):
    """
    Serve the QR tools page.
    """
    return templates.TemplateResponse("qr_tools.html", {"request": request})

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    Returns:
        dict: Simple status message.
    """
    return {"status": "ok", "message": "AXA ADAPT API is running"}

@app.get("/qr/{qr_id}", response_class=HTMLResponse)
async def view_health_summary(qr_id: str, request: Request):
    """
    Unified QR scan endpoint for both basic (static) and full (tokenized) QR codes.
    - For basic: qr_id is static_id, loads qr_basic_{static_id}.json
    - For full: qr_id is token, loads qr_token_{token}.json and checks expiry
    """
    try:
        # Try full (token) QR first
        token_path = OUTPUT_DIR / f"qr_token_{qr_id}.json"
        static_path = OUTPUT_DIR / f"qr_basic_{qr_id}.json"
        token_data = None
        qr_type = None
        
        if token_path.exists():
            try:
                token_data = validate_token(qr_id, output_dir=OUTPUT_DIR)
                qr_type = "full"
            except TokenExpiredError:
                return HTMLResponse("<h2>This QR code has expired.</h2>", status_code=410)
            except TokenValidationError as e:
                logger.warning(f"Invalid token {qr_id}: {e}")
                # Continue to check for static QR
        
        if token_data is None and static_path.exists():
            try:
                with open(static_path) as f:
                    token_data = json.load(f)
                qr_type = "basic"
            except json.JSONDecodeError:
                logger.error(f"Invalid static QR data: {static_path}")
        
        if not token_data:
            return HTMLResponse(
                "<h2>QR code not found or invalid.</h2>",
                status_code=404
            )
        
        # Get user profile
        user_id = token_data.get("user_id")
        if not user_id:
            logger.error("No user_id in token data")
            return HTMLResponse("<h2>Invalid QR code data.</h2>", status_code=400)
        
        profile = load_user_profile(user_id.split('_')[-1])
        consent = token_data.get("consent", {})
        
        # Load risk report if available
        risk_report_path = OUTPUT_DIR / f"risk_report_{user_id}.json"
        risk_score = None
        hazards = None
        recommendation = None
        
        if risk_report_path.exists():
            try:
                with open(risk_report_path) as rf:
                    report = json.load(rf)
                    risk_score = report.get("score")
                    hazards = report.get("hazards")
                    recommendation = report.get("recommendation")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading risk report: {e}")
                risk_score = 50  # Default score if there's an error
        else:
            risk_score = 50  # Default score if no report exists
            
        # Prepare the response data
        response_data = {
            "user_id": user_id,
            "profile": profile,
            "consent": consent,
            "risk_score": risk_score,
            "hazards": hazards or [],
            "recommendation": recommendation or "No specific recommendations available."
        }
        
        # For now, return a simple HTML response
        # In a real application, you would use a proper templating engine
        html_content = f"""
        <html>
            <head><title>Health Summary</title></head>
            <body>
                <h1>Health Summary for {profile.get('name', 'User')}</h1>
                <h2>Risk Score: {risk_score}/100</h2>
                <h3>Recommendations:</h3>
                <p>{recommendation or 'No specific recommendations available.'}</p>
                <h3>Detected Hazards:</h3>
                <ul>
                    {"".join(f'<li>{hazard}</li>' for hazard in (hazards or []))}
                </ul>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
        
    except Exception as e:
        logger.error(f"Error in view_health_summary: {e}")
        return HTMLResponse(
            content="<h2>An error occurred while processing your request.</h2>",
            status_code=500
        )
        hazards = [
            {"object": "cord", "location": "hallway", "reason": "Mobility and cognition increase risk"},
            {"object": "rug", "location": "bedroom", "reason": "Mobility increases risk"}
        ]
        recommendation = "Remove loose cords and rugs; re-scan in 30 days"
    last_scan = profile.get("last_updated", "-")
    # Build HTML based on consent
    blocks = []
    if consent.get("name", False):
        blocks.append(f"<b>Name:</b> {profile['personal_info']['name']}")
    if consent.get("risk_score", False):
        blocks.append(f"<b>Fall Risk Score:</b> {risk_score}")
    if consent.get("hazards", False):
        hazards_html = "<ul>" + "".join([f"<li>{h['object'].title()} in {h['location']} ({h['reason']})</li>" for h in hazards]) + "</ul>"
        blocks.append(f"<b>Recent Hazards:</b> {hazards_html}")
    if consent.get("conditions", False):
        blocks.append(f"<b>Conditions:</b> Vision: {profile['health_conditions']['vision']['notes']}, Mobility: {profile['health_conditions']['mobility']['notes']}")
    if consent.get("emergency_contact", False):
        ec = profile['emergency_contacts'][0]
        blocks.append(f"<b>Emergency Contact:</b> {ec['name']} ({ec['relationship']}), {ec['phone']}")
    if consent.get("care_directives", False):
        blocks.append(f"<b>Care Directives:</b> None provided")  # Stub
    blocks.append(f"<b>Last Scan Date:</b> {last_scan}")
    if recommendation and (consent.get("risk_score") or consent.get("hazards")):
        blocks.append(f"<b>Recommendation:</b> {recommendation}")
    # Log access with IP address
    log_entry = {
        "event": "access",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "qr_type": qr_type,
        "qr_id": qr_id,
        "user_id": user_id,
        "ip": request.client.host if request and request.client else None,
        "fields_shown": [k for k,v in consent.items() if v],
        "consent_snapshot": consent
    }
    with open("outputs/qr_access_log.csv", "a") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    html = """
    <html><head><title>AXA Health Summary</title></head><body>
    <h2>AXA Health Summary</h2>
    <div style='font-size:1.2em;'>
    """ + "<br>".join(blocks) + "</div></body></html>"
    return HTMLResponse(html)

@app.get("/qr-access-log")
def get_qr_access_log(user_id: str = None, token: str = None, as_json: bool = False):
    """Admin: View QR access log, filter by user_id or token, return JSON or CSV."""
    log_path = "outputs/qr_access_log.csv"
    if not os.path.exists(log_path):
        return {"log": []} if as_json else "timestamp,token,user_id,ip,fields_shown,consent_snapshot\n"
    entries = []
    with open(log_path) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if user_id and entry.get("user_id") != user_id:
                    continue
                if token and entry.get("token") != token:
                    continue
                entries.append(entry)
            except Exception:
                continue
    if as_json:
        return {"log": entries}
    # else return CSV
    import csv
    from io import StringIO
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=["timestamp","token","user_id","ip","fields_shown","consent_snapshot"])
    writer.writeheader()
    for e in entries:
        writer.writerow(e)
    return csvfile.getvalue()

@app.post("/revoke-qr")
async def revoke_qr(request: Request):
    data = await request.json()
    token = data.get("token")
    token_path = f"outputs/qr_token_{token}.json"
    if not os.path.exists(token_path):
        return {"error": "Token not found"}
    with open(token_path) as f:
        token_data = json.load(f)
    token_data["revoked"] = True
    with open(token_path, "w") as f:
        json.dump(token_data, f)
    # Log revocation event
    log_entry = {
        "event": "revoke",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "token": token,
        "user_id": token_data.get("user_id")
    }
    with open("outputs/qr_access_log.csv", "a") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    return {"status": "revoked", "token": token}

@app.post("/api/generate-qr", response_model=Dict)
async def generate_qr_code_endpoint(request: QRGenerateRequest):
    """
    Generate a secure QR code for health data access.
    
    Args:
        request: QR generation parameters including user_id and access type
        
    Returns:
        JSON with QR code URL and metadata
    """
    try:
        # Generate secure URL with token
        qr_url = generate_secure_url(
            user_id=request.user_id,
            expiry_hours=request.expiry_hours,
            output_dir=OUTPUT_DIR,
            access_type=request.access_type,
            metadata=request.metadata or {}
        )
        
        # Generate QR code image
        qr_filename = f"qr_{request.user_id}_{int(datetime.utcnow().timestamp())}.png"
        qr_path = OUTPUT_DIR / qr_filename
        
        create_qr_code(
            data=qr_url,
            filename=qr_path,
            box_size=10,
            border=4,
            fill_color="black",
            back_color="white"
        )
        
        return {
            "status": "success",
            "qr_url": qr_url,
            "image_url": f"/static/{qr_filename}",
            "expires_at": (datetime.utcnow() + timedelta(hours=request.expiry_hours)).isoformat()
        }
        
    except QRCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error generating QR code")
        raise HTTPException(status_code=500, detail="Failed to generate QR code")

@app.on_event("startup")
async def startup_event():
    """Initialize application services on startup."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Clean up any expired tokens
    expired, stale = cleanup_expired_tokens(output_dir=OUTPUT_DIR)
    logger.info(f"Cleaned up {expired} expired and {stale} stale tokens on startup")
    
    # Preload model (optional)
    # get_model()

# Scheduled task for cleaning up expired tokens (runs daily)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    cleanup_expired_tokens,
    'interval',
    hours=24,
    args=[OUTPUT_DIR],
    id='cleanup_tokens',
    name='Clean up expired tokens',
    replace_existing=True
)
scheduler.start()

# Handle application shutdown
import atexit
atexit.register(lambda: scheduler.shutdown())
import os

# Predefined data blocks for consent
QR_DATA_BLOCKS = [
    {"key": "name", "label": "Name", "gdpr": "Personal data", "consent_required": False},
    {"key": "emergency_contact", "label": "Emergency Contact", "gdpr": "Personal data", "consent_required": True},
    {"key": "risk_score", "label": "Fall Risk Score", "gdpr": "Health-inferred", "consent_required": True},
    {"key": "hazards", "label": "Detected Hazards", "gdpr": "Health-inferred", "consent_required": True},
    {"key": "conditions", "label": "Conditions (vision, mobility)", "gdpr": "Health data", "consent_required": True},
    {"key": "care_directives", "label": "Care Directives", "gdpr": "Medical data", "consent_required": True},
]

# Default public blocks for emergency QR
QR_PUBLIC_BLOCKS = ["name", "risk_score", "emergency_contact"]

from fastapi import Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw
import io

@app.post("/generate-qr-card")
async def generate_qr_card(card_type: str = Form(...), photo: UploadFile = File(...), user_id: str = Form("demo")):
    """
    Generate a QR card image (fridge or family) with uploaded photo and QR overlay.
    - card_type: 'fridge' or 'family'
    - photo: uploaded image
    - user_id: for QR lookup (future: auth)
    """
    # Card sizes
    size = (800, 600) if card_type == "fridge" else (1600, 1200)
    # Load uploaded photo
    image_bytes = await photo.read()
    bg = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    bg = bg.resize(size, Image.LANCZOS)
    # Load QR image (use most recent for user)
    import glob
    qr_files = sorted(glob.glob(f"outputs/qr_*_{user_id}_*.png"), key=os.path.getmtime, reverse=True)
    qr_img = None
    if qr_files:
        qr_img = Image.open(qr_files[0]).convert("RGBA")
        qr_img = qr_img.resize((160, 160), Image.LANCZOS)
    # Card background (fridge: white with AXA red bar, family: full photo)
    if card_type == "fridge":
        card = Image.new("RGB", size, (255,255,255))
        # AXA red bar at top
        draw = ImageDraw.Draw(card)
        draw.rectangle([0,0,size[0],40], fill="#e60028")
        card.paste(bg, (0,40))
    else:
        card = bg.copy()
    # Paste QR bottom-right
    if qr_img:
        qr_x = size[0] - 160 - 32
        qr_y = size[1] - 160 - 32
        card.paste(qr_img, (qr_x, qr_y), qr_img)
        # AXA logo watermark above QR (fridge only)
        if card_type == "fridge":
            logo_path = "axa_app_mvp/static/axa_logo.png"
            if os.path.exists(logo_path):
                try:
                    logo = Image.open(logo_path).convert("RGBA")
                    logo_w = 80
                    logo_h = int(logo.size[1] * (logo_w / logo.size[0]))
                    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
                    logo_x = qr_x + 40
                    logo_y = qr_y - logo_h - 8
                    card.paste(logo, (logo_x, logo_y), logo)
                except Exception:
                    pass
    # Save result
    out_path = f"outputs/{card_type}_card_{user_id}.png"
    card.save(out_path)
    # Return image URL for preview
    return JSONResponse({"image_url": f"/{out_path}"})

@app.get("/qr-basic/{user_id}", response_class=HTMLResponse)
def qr_basic_view(user_id: str, request: Request):
    """
    Public emergency QR view: only default public blocks, no token required.
    """
    # Find a basic QR metadata file for this user with public blocks
    static_id = f"{user_id}_" + "_".join(sorted(QR_PUBLIC_BLOCKS))
    meta_path = f"outputs/qr_basic_{static_id}.json"
    outcome = "success"
    if not os.path.exists(meta_path):
        outcome = "not_found"
        html = "<h2>Public emergency QR not found.</h2>"
    else:
        with open(meta_path) as f:
            meta = json.load(f)
        consent = meta.get("consent", {})
        # Only allow public blocks
        filtered_consent = {k: v for k, v in consent.items() if k in QR_PUBLIC_BLOCKS and v}
        # Load user profile
        profile_path = f"axa_app_mvp/profiles/health_profile_{user_id.split('_')[-1]}.json"
        if not os.path.exists(profile_path):
            profile_path = f"axa_app_mvp/profiles/health_profile_maria.json"
        with open(profile_path) as f:
            profile = json.load(f)
        # Load risk report if available
        risk_report_path = f"axa_app_mvp/outputs/risk_report_{user_id}.json"
        risk_score = None
        if os.path.exists(risk_report_path):
            with open(risk_report_path) as rf:
                report = json.load(rf)
                risk_score = report.get("score")
        else:
            risk_score = 72
        blocks = []
        if filtered_consent.get("name"):
            blocks.append(f"<b>Name:</b> {profile['personal_info']['name']}")
        if filtered_consent.get("risk_score"):
            blocks.append(f"<b>Fall Risk Score:</b> {risk_score}")
        if filtered_consent.get("emergency_contact"):
            ec = profile['emergency_contacts'][0]
            blocks.append(f"<b>Emergency Contact:</b> {ec['name']} ({ec['relationship']}), {ec['phone']}")
        html = """
        <html><head><title>AXA Emergency QR</title></head><body>
        <h2>AXA Emergency QR</h2>
        <div style='font-size:1.2em;'>
        """ + "<br>".join(blocks) + "</div></body></html>"
    # Log access
    log_entry = {
        "event": "qr_basic_scan",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "ip": request.client.host if request and request.client else None,
        "fields_shown": QR_PUBLIC_BLOCKS,
        "outcome": outcome
    }
    with open("outputs/qr_access_log.csv", "a") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    return HTMLResponse(html)

@app.get("/qr-deep/{user_id}", response_class=HTMLResponse)
def qr_deep_view(user_id: str, request: Request, token: str = Query(None)):
    """
    Full caregiver QR view: requires valid token as query param, shows all consented blocks.
    """
    meta_path = f"outputs/qr_token_{token}.json"
    outcome = "success"
    if not token or not os.path.exists(meta_path):
        outcome = "invalid_or_expired"
        html = "<h2>QR code not found or expired.</h2>"
    else:
        with open(meta_path) as f:
            meta = json.load(f)
        # Check expiry/revocation
        expires = meta.get("expires")
        if expires and datetime.fromisoformat(expires.replace("Z","")) < datetime.utcnow():
            outcome = "expired"
            html = "<h2>This QR code has expired.</h2>"
        elif meta.get("revoked", False):
            outcome = "revoked"
            html = "<h2>This QR code has been revoked.</h2>"
        else:
            consent = meta.get("consent", {})
            # Load user profile
            profile_path = f"axa_app_mvp/profiles/health_profile_{user_id.split('_')[-1]}.json"
            if not os.path.exists(profile_path):
                profile_path = f"axa_app_mvp/profiles/health_profile_maria.json"
            with open(profile_path) as f:
                profile = json.load(f)
            # Load risk report if available
            risk_report_path = f"axa_app_mvp/outputs/risk_report_{user_id}.json"
            risk_score = None
            hazards = None
            recommendation = None
            if os.path.exists(risk_report_path):
                with open(risk_report_path) as rf:
                    report = json.load(rf)
                    risk_score = report.get("score")
                    hazards = report.get("hazards")
                    recommendation = report.get("recommendation")
            else:
                risk_score = 72
                hazards = []
                recommendation = None
            blocks = []
            if consent.get("name"):
                blocks.append(f"<b>Name:</b> {profile['personal_info']['name']}")
            if consent.get("risk_score"):
                blocks.append(f"<b>Fall Risk Score:</b> {risk_score}")
            if consent.get("hazards") and hazards:
                hazards_html = "<ul>" + "".join([f"<li>{h['object'].title()} in {h['location']} ({h['reason']})</li>" for h in hazards]) + "</ul>"
                blocks.append(f"<b>Recent Hazards:</b> {hazards_html}")
            if consent.get("conditions"):
                blocks.append(f"<b>Conditions:</b> Vision: {profile['health_conditions']['vision']['notes']}, Mobility: {profile['health_conditions']['mobility']['notes']}")
            if consent.get("emergency_contact"):
                ec = profile['emergency_contacts'][0]
                blocks.append(f"<b>Emergency Contact:</b> {ec['name']} ({ec['relationship']}), {ec['phone']}")
            if consent.get("care_directives"):
                blocks.append(f"<b>Care Directives:</b> None provided")  # Stub
            if recommendation and (consent.get("risk_score") or consent.get("hazards")):
                blocks.append(f"<b>Recommendation:</b> {recommendation}")
            html = """
            <html><head><title>AXA Caregiver QR</title></head><body>
            <h2>AXA Caregiver QR</h2>
            <div style='font-size:1.2em;'>
            """ + "<br>".join(blocks) + "</div></body></html>"
    # Log access
    log_entry = {
        "event": "qr_deep_scan",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "token": token,
        "ip": request.client.host if request and request.client else None,
        "fields_shown": list(consent.keys()) if outcome == "success" else [],
        "outcome": outcome
    }
    with open("outputs/qr_access_log.csv", "a") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    return HTMLResponse(html)

@app.post("/generate-qr/{user_id}")
async def generate_qr(user_id: str, request: Request):
    """
    Generate a QR code for health summary access.
    Request JSON:
      - access_type: 'basic' or 'full'
      - consent: list of data block keys to include
      - (optional) expiry_hours: int (default 24 for full)
    """
    data = await request.json()
    access_type = data.get("access_type", "basic")
    consent_blocks = data.get("consent", [])  # list of keys
    expiry_hours = int(data.get("expiry_hours", 24))
    # Validate consent blocks
    valid_keys = {b["key"] for b in QR_DATA_BLOCKS}
    consent_blocks = [k for k in consent_blocks if k in valid_keys]
    # Build consent structure
    consent = {k: True for k in consent_blocks}
    # URL and token logic
    if access_type == "basic":
        # Static public URL: always the same for this user/profile/consent combo
        static_id = f"{user_id}_" + "_".join(sorted(consent_blocks))
        url = f"https://axa-safestep.com/qr/basic/{static_id}"
        token = None
        expires = None
        token_data = {
            "access_type": "basic",
            "user_id": user_id,
            "consent": consent,
            "static_id": static_id,
            "created": datetime.utcnow().isoformat() + "Z"
        }
        meta_path = f"outputs/qr_basic_{static_id}.json"
    else:
        # Full access: generate token and expiry
        from uuid import uuid4
        token = str(uuid4())
        expires = (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat() + "Z"
        url = f"https://axa-safestep.com/qr/{token}"
        token_data = {
            "access_type": "full",
            "token": token,
            "user_id": user_id,
            "consent": consent,
            "created": datetime.utcnow().isoformat() + "Z",
            "expires": expires
        }
        meta_path = f"outputs/qr_token_{token}.json"
    # Store metadata
    with open(meta_path, "w") as f:
        json.dump(token_data, f)
    # Generate QR code
    import qrcode
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    qr_filename = f"outputs/qr_{access_type}_{user_id}_{token or static_id}.png"
    img.save(qr_filename)
    # Log event
    log_entry = {
        "event": "generate",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "access_type": access_type,
        "token": token,
        "user_id": user_id,
        "consent_blocks": consent_blocks,
        "meta_path": meta_path
    }
    with open("outputs/qr_access_log.csv", "a") as logf:
        logf.write(json.dumps(log_entry) + "\n")
    return {
        "qr_image": qr_filename,
        "url": url,
        "token": token,
        "expires": expires,
        "access_type": access_type,
        "consent_blocks": consent_blocks
    }

from fastapi import Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
from pathlib import Path

# QR Tool data models
class QRProfileForm(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    conditions: List[str] = []
    medications: str = ""
    allergies: str = ""
    emergency_contact: str
    emergency_phone: str
    relationship: str

class QRContentSelection(BaseModel):
    include_medical: bool = True
    include_medications: bool = True
    include_allergies: bool = True
    include_emergency: bool = True

class QRPrivacySettings(BaseModel):
    privacy: str  # 'public' or 'private'
    expiry: str = '24'  # hours or 'custom'
    custom_expiry_date: Optional[str] = None

class QRGenerateData(BaseModel):
    profile: Dict[str, Any]
    content: Dict[str, bool]
    privacy: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# QR Tool utility functions
def save_qr_data(user_id: str, qr_data: Dict[str, Any], output_dir: str = "axa_app_mvp/outputs") -> str:
    """Save QR data to a JSON file and return the filename."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"qr_data_{user_id}_{int(datetime.utcnow().timestamp())}.json"
    filepath = Path(output_dir) / filename
    
    with open(filepath, 'w') as f:
        json.dump(qr_data, f, indent=2)
    
    return str(filepath)

def generate_qr_code_url(qr_data: Dict[str, Any], base_url: str = "https://axa-adapt.com") -> str:
    """Generate a secure URL for the QR code."""
    qr_id = str(uuid.uuid4())
    # In a real implementation, you would store this in a database
    # For now, we'll just return a URL with a query parameter
    return f"{base_url}/qr/view/{qr_id}"

from fastapi import Request, Form, Depends
from axa_app_mvp.logic.hazard_scoring import (
    load_risk_matrix, load_thresholds, load_detection_mapping,
    map_detected_objects_to_hazards, score_hazards
)

# ADAPT Tool Routes
@app.get("/adapt-tool/start", response_class=HTMLResponse)
async def adapt_tool_start(request: Request):
    """
    Serve the ADAPT Tool start page.
    """
    return templates.TemplateResponse("adapt_tool_start.html", {"request": request, "current_date": datetime.now().strftime("%B %d, %Y")})

@app.get("/adapt-tool/upload", response_class=HTMLResponse)
async def adapt_tool_upload(request: Request):
    """
    Serve the ADAPT Tool room photo upload page.
    """
    return templates.TemplateResponse("adapt_tool_upload.html", {"request": request, "current_date": datetime.now().strftime("%B %d, %Y")})

@app.get("/adapt-tool/profile", response_class=HTMLResponse)
async def adapt_tool_profile(request: Request):
    """
    Serve the ADAPT Tool profile questions page.
    """
    return templates.TemplateResponse("adapt_tool_profile.html", {"request": request, "current_date": datetime.now().strftime("%B %d, %Y")})

@app.get("/adapt-tool/results", response_class=HTMLResponse)
async def adapt_tool_results(request: Request):
    """
    Serve the ADAPT Tool results page with fall risk assessment.
    """
    return templates.TemplateResponse("adapt_tool_results.html", {
        "request": request, 
        "current_date": datetime.now().strftime("%B %d, %Y"),
        "current_year": datetime.now().year
    })

@app.post("/api/assess-hazards", response_model=Dict)
async def assess_hazards(
    request: Request,
    sitting_room: UploadFile = File(None),
    bathroom: UploadFile = File(None),
    hallway: UploadFile = File(None),
    steps: UploadFile = File(None),
    bedroom: UploadFile = File(None),
    profile_json: str = Form(...)
):
    """
    Accepts room images and user profile, returns fall hazard risk assessment.
    
    Args:
        sitting_room: Image of the sitting room
        bathroom: Image of the bathroom
        hallway: Image of the hallway
        steps: Image of the stairs/steps
        bedroom: Image of the bedroom
        profile_json: JSON string containing user profile information
        
    Returns:
        JSON with risk assessment results
    """
    try:
        # Parse and validate profile
        try:
            profile = json.loads(profile_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid profile JSON")
        
        # Process uploaded images
        room_files = {
            "sitting_room": sitting_room,
            "bathroom": bathroom,
            "hallway": hallway,
            "steps": steps,
            "bedroom": bedroom,
        }
        
        # Filter out None values (not provided files)
        room_files = {k: v for k, v in room_files.items() if v is not None}
        
        if not room_files:
            raise HTTPException(status_code=400, detail="No images provided")
        
        # Load YOLO model
        model = get_model()
        
        # Process each image
        detected_objects = []
        for room_name, file in room_files.items():
            try:
                contents = await file.read()
                img_np = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
                if img_np is None:
                    logger.warning(f"Failed to decode image for {room_name}")
                    continue
                
                # Run object detection
                results = model(img_np)
                
                # Process detection results
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        name = model.names[cls_id]
                        confidence = float(box.conf[0])
                        
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        
                        detected_objects.append({
                            "object": name,
                            "location": room_name.replace('_', ' '),
                            "confidence": confidence,
                            "bbox": {
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2
                            }
                        })
                        
                logger.info(f"Processed {room_name}: {len(detected_objects)} objects detected")
                
            except Exception as e:
                logger.error(f"Error processing {room_name}: {e}")
                continue
        
        if not detected_objects:
            return {
                "status": "success",
                "message": "No hazards detected",
                "score": 0,
                "risk_level": "Low",
                "hazards": []
            }
        
        # Load risk assessment data
        try:
            matrix_path = BASE_DIR / "axa_app_mvp" / "logic" / "risk_matrix_v1.csv"
            thresholds_path = BASE_DIR / "axa_app_mvp" / "logic" / "risk_score_thresholds.csv"
            mapping_path = BASE_DIR / "axa_app_mvp" / "logic" / "detection_to_hazard.csv"
            
            matrix = load_risk_matrix(matrix_path)
            thresholds = load_thresholds(thresholds_path)
            mapping = load_detection_mapping(mapping_path)
            
            # Map detected objects to hazards and score them
            hazards = map_detected_objects_to_hazards(detected_objects, mapping)
            report = score_hazards(hazards, profile, matrix, thresholds)
            
            # Add timestamp and metadata
            report["timestamp"] = datetime.utcnow().isoformat()
            report["detected_objects"] = detected_objects
            report["status"] = "success"
            
            return report
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in risk assessment: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in hazard assessment")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    return report
