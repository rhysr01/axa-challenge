from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime

from gen_qr import generate_qr_code, validate_user_payload, generate_axa_qr

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
    Generate QR code for AXA user data.
    
    Accepts JSON payload with user information and returns the generated QR code.
    """
    try:
        # Convert request to dictionary for validation
        payload = request.dict()
        
        # Validate payload
        if not validate_user_payload(payload):
            raise HTTPException(
                status_code=400,
                detail="Invalid payload. Must include user_id and either axa_id_url or contact info."
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
        
        # Generate file URL (relative path for API response)
        file_url = f"/qr-codes/{os.path.basename(file_path)}"
        
        return QRGenerateResponse(
            success=True,
            user_id=request.user_id,
            file_path=file_path,
            file_url=file_url,
            message="QR code generated successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
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
        "service": "axa-qr-generator"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)