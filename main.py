"""
FastAPI app for AXA ADAPT.

Receives 5 room images, runs YOLOv8 detection, and returns structured fall hazards
(tagged by room, with confidence and severity).
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import numpy as np
import cv2
from ultralytics import YOLO
from axa_app_mvp.logic.qr_utils import generate_secure_url, create_qr_code

@app.get("/qr/{qr_id}", response_class=HTMLResponse)
def view_health_summary(qr_id: str, request: Request):
    """
    Unified QR scan endpoint for both basic (static) and full (tokenized) QR codes.
    - For basic: qr_id is static_id, loads qr_basic_{static_id}.json
    - For full: qr_id is token, loads qr_token_{token}.json and checks expiry
    """
    # Try full (token) QR first
    token_path = f"outputs/qr_token_{qr_id}.json"
    static_path = f"outputs/qr_basic_{qr_id}.json"
    token_data = None
    qr_type = None
    if os.path.exists(token_path):
        with open(token_path) as f:
            token_data = json.load(f)
        qr_type = "full"
        # Check expiry
        expires = token_data.get("expires")
        if expires and datetime.fromisoformat(expires.replace("Z","")) < datetime.utcnow():
            return HTMLResponse("<h2>This QR code has expired.</h2>", status_code=410)
        if token_data.get("revoked", False):
            return HTMLResponse("<h2>This QR code has been revoked.</h2>", status_code=403)
    elif os.path.exists(static_path):
        with open(static_path) as f:
            token_data = json.load(f)
        qr_type = "basic"
    else:
        return HTMLResponse("<h2>QR code not found or expired.</h2>", status_code=404)
    user_id = token_data.get("user_id")
    consent = token_data.get("consent", {})
    # Load user profile
    profile_path = f"axa_app_mvp/profiles/health_profile_{user_id.split('_')[-1]}.json"
    if not os.path.exists(profile_path):
        profile_path = f"axa_app_mvp/profiles/health_profile_maria.json"  # fallback for demo
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
        risk_score = 72  # fallback
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

app = FastAPI()

# Allow all origins for now (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolov8n.pt")  # Replace with your model file if needed

@app.get("/")
def root():
    """
    Health check endpoint.
    Returns:
        dict: Simple status message.
    """
    return {"message": "AXA ADAPT backend is running."}

from fastapi import Request
from fastapi.responses import HTMLResponse
import json
from datetime import datetime, timedelta
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

from fastapi import Request
from axa_app_mvp.logic.hazard_scoring import (
    load_risk_matrix, load_thresholds, load_detection_mapping,
    map_detected_objects_to_hazards, score_hazards
)

@app.post("/process-multi-room")
async def detect_hazards(
    request: Request,
    sittingRoom: UploadFile = File(...),
    bathroom: UploadFile = File(...),
    hallway: UploadFile = File(...),
    steps: UploadFile = File(...),
    bedroom: UploadFile = File(...)
):
    """
    Accepts 5 labeled room images and user profile, returns full risk report.
    """
    # Parse JSON body for user profile
    form = await request.form()
    profile_json = form.get("profile")
    if not profile_json:
        return {"error": "Missing profile in form-data"}
    import json
    profile = json.loads(profile_json)

    room_files = {
        "sitting room": sittingRoom,
        "bathroom": bathroom,
        "hallway": hallway,
        "steps": steps,
        "bedroom": bedroom,
    }

    detected = []
    for room, file in room_files.items():
        contents = await file.read()
        img_np = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        results = model(img_np)
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                name = model.names[cls_id]
                detected.append({
                    "object": name,
                    "location": room
                })

    # Load logic data
    matrix = load_risk_matrix("axa_app_mvp/logic/risk_matrix_v1.csv")
    thresholds = load_thresholds("axa_app_mvp/logic/risk_score_thresholds.csv")
    mapping = load_detection_mapping("axa_app_mvp/logic/detection_to_hazard.csv")

    # Map detected objects to hazards
    hazards = map_detected_objects_to_hazards(detected, mapping)

    # Score hazards
    report = score_hazards(hazards, profile, matrix, thresholds)
    return report
