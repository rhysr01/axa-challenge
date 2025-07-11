from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os
import json
import uuid
from datetime import datetime

from gen_qr import generate_qr_code, validate_user_payload, generate_axa_qr
from gdpr_compliance import (
    regulatory_logger, 
    data_exporter, 
    ConsentManager, 
    DATA_RESIDENCY_REGION
)

app = FastAPI(
    title="AXA QR Code Generator",
    description="Generate QR codes for AXA client onboarding",
    version="1.0.0"
)


class QRGenerateRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    axa_id_url: Optional[str] = Field(None, description="AXA ID URL for the user")
    contact: Optional[Dict[str, Any]] = Field(None, description="Contact information")
    output_format: str = Field("png", description="Output format (png or svg)")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "axa_id_url": "https://axa.com/profile/user_12345",
                "contact": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890"
                },
                "output_format": "png"
            }
        }


class QRGenerateResponse(BaseModel):
    success: bool
    user_id: str
    file_path: str
    file_url: str
    message: str
    timestamp: str
    request_id: str
    data_residency: str
    consent_verified: bool


class DataExportResponse(BaseModel):
    user_id: str
    export_timestamp: str
    data_residency: str
    consent_status: bool
    qr_codes: list
    activity_logs: list
    export_metadata: Dict[str, Any]


class ConsentStatusResponse(BaseModel):
    user_id: str
    has_consent: bool
    data_residency: str
    consented_users_count: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "AXA QR Code Generator API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/generate", response_model=QRGenerateResponse)
async def generate_qr(request: QRGenerateRequest):
    """
    Generate QR code for AXA user data with GDPR compliance.
    
    Checks user consent before processing and logs all actions for audit trail.
    """
    # Generate unique request ID for audit trail
    request_id = str(uuid.uuid4())
    
    try:
        # Convert request to dictionary for validation
        payload = request.dict()
        
        # Validate payload
        if not validate_user_payload(payload):
            raise HTTPException(
                status_code=400,
                detail="Invalid payload. Must include user_id and either axa_id_url or contact info."
            )
        
        # GDPR: Check user consent before processing
        has_consent = ConsentManager.has_consent(request.user_id)
        if not has_consent:
            # Log the denied request for audit trail
            regulatory_logger.log_qr_generation(
                user_id=request.user_id,
                payload=payload,
                request_id=request_id,
                consent_verified=False
            )
            raise HTTPException(
                status_code=403,
                detail=f"User {request.user_id} has not given consent for data processing. "
                       f"Contact AXA support to update consent status."
            )
        
        # Generate QR code
        if request.axa_id_url:
            file_path = generate_axa_qr(
                axa_id_url=request.axa_id_url,
                user_id=request.user_id,
                contact_info=request.contact
            )
        else:
            # Generate with contact info only
            user_data = {
                "user_id": request.user_id,
                "type": "axa_contact"
            }
            if request.contact:
                user_data["contact"] = request.contact
            
            file_path = generate_qr_code(
                user_data=user_data,
                user_id=request.user_id,
                output_format=request.output_format
            )
        
        # GDPR: Log successful QR generation for audit trail
        regulatory_logger.log_qr_generation(
            user_id=request.user_id,
            payload=payload,
            request_id=request_id,
            consent_verified=True
        )
        
        # Generate file URL (relative path for API response)
        file_url = f"/qr-codes/{os.path.basename(file_path)}"
        
        return QRGenerateResponse(
            success=True,
            user_id=request.user_id,
            file_path=file_path,
            file_url=file_url,
            message="QR code generated successfully",
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data_residency=DATA_RESIDENCY_REGION,
            consent_verified=True
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like consent denial)
        raise
    except Exception as e:
        # Log unexpected errors
        regulatory_logger.log_qr_generation(
            user_id=request.user_id,
            payload=payload,
            request_id=request_id,
            consent_verified=has_consent if 'has_consent' in locals() else False
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )


@app.get("/qr-codes/{filename}")
async def get_qr_code(filename: str):
    """
    Serve generated QR code files.
    """
    file_path = os.path.join("qr-codes", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="QR code file not found")
    
    # Determine media type based on file extension
    if filename.lower().endswith('.svg'):
        media_type = "image/svg+xml"
    else:
        media_type = "image/png"
    
    return FileResponse(file_path, media_type=media_type)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "axa-qr-generator",
        "data_residency": DATA_RESIDENCY_REGION,
        "gdpr_compliance": "enabled"
    }


@app.get("/export-data/{user_id}", response_model=DataExportResponse)
async def export_user_data(user_id: str):
    """
    GDPR: Export all data associated with a user.
    
    Returns all QR codes, activity logs, and metadata for the specified user.
    This endpoint fulfills the GDPR "right to data portability" requirement.
    """
    # Generate request ID for audit trail
    request_id = str(uuid.uuid4())
    
    try:
        # Log the data export request
        regulatory_logger.log_data_export(user_id, request_id)
        
        # Export user data
        export_data = data_exporter.export_user_data(user_id)
        
        return DataExportResponse(**export_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export data for user {user_id}: {str(e)}"
        )


@app.get("/consent-status/{user_id}", response_model=ConsentStatusResponse)
async def get_consent_status(user_id: str):
    """
    Check GDPR consent status for a user.
    """
    has_consent = ConsentManager.has_consent(user_id)
    consented_count = len(ConsentManager.list_consented_users())
    
    return ConsentStatusResponse(
        user_id=user_id,
        has_consent=has_consent,
        data_residency=DATA_RESIDENCY_REGION,
        consented_users_count=consented_count
    )


@app.post("/admin/grant-consent/{user_id}")
async def grant_user_consent(user_id: str):
    """
    Admin endpoint: Grant consent for a user (for pilot user setup).
    
    In production, this would be replaced with proper consent capture flows.
    """
    ConsentManager.grant_consent(user_id)
    
    return {
        "message": f"Consent granted for user {user_id}",
        "user_id": user_id,
        "has_consent": True,
        "timestamp": datetime.now().isoformat(),
        "data_residency": DATA_RESIDENCY_REGION
    }


@app.get("/admin/consented-users")
async def list_consented_users():
    """
    Admin endpoint: List all users who have given consent.
    """
    consented_users = ConsentManager.list_consented_users()
    
    return {
        "consented_users": consented_users,
        "total_count": len(consented_users),
        "data_residency": DATA_RESIDENCY_REGION,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)