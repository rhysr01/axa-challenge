from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import os
import json
import uuid
import tempfile
from datetime import datetime

from room_detector import RoomDetector, RoomType, DetectionMethod, DetectionResult

app = FastAPI(
    title="AXA Room Detection API",
    description="Detect and classify room types using various methods",
    version="1.0.0"
)

# Global room detector instance
room_detector = RoomDetector()

class ImageDetectionRequest(BaseModel):
    image_url: Optional[str] = Field(None, description="URL to image file")
    


class ManualDetectionRequest(BaseModel):
    room_type: str = Field(..., description="Room type to set manually")
    room_id: Optional[str] = Field(None, description="Room identifier")
    building_id: Optional[str] = Field(None, description="Building identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "room_type": "meeting_room",
                "room_id": "MR-A-101",
                "building_id": "AXA-HQ-Paris"
            }
        }

class DetectionResponse(BaseModel):
    detection_id: str
    room_type: str
    confidence: float
    detection_method: str
    timestamp: str
    metadata: Dict[str, Any]
    room_id: Optional[str] = None
    building_id: Optional[str] = None

class DetectionHistoryResponse(BaseModel):
    detections: List[DetectionResponse]
    total_count: int

class RoomStatisticsResponse(BaseModel):
    total_detections: int
    room_type_distribution: Dict[str, int]
    detection_method_distribution: Dict[str, int]
    average_confidence: float
    most_common_room: Optional[str]

def detection_result_to_response(result: DetectionResult) -> DetectionResponse:
    """Convert DetectionResult to API response format."""
    return DetectionResponse(
        detection_id=str(uuid.uuid4()),
        room_type=result.room_type.value,
        confidence=result.confidence,
        detection_method=result.detection_method.value,
        timestamp=result.timestamp,
        metadata=result.metadata,
        room_id=result.room_id,
        building_id=result.building_id
    )

@app.get("/")
async def root():
    """API information endpoint."""
    return {
        "message": "AXA Room Detection API",
        "status": "operational",
        "version": "1.0.0",
        "available_room_types": [room_type.value for room_type in RoomType],
        "available_detection_methods": [method.value for method in DetectionMethod]
    }

@app.post("/detect/image", response_model=DetectionResponse)
async def detect_room_from_image(file: UploadFile = File(...)):
    """
    Detect room type from uploaded image.
    
    Upload an image file and get room type detection results.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        try:
            # Perform detection
            result = room_detector.detect_room_from_image(temp_path)
            return detection_result_to_response(result)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")



@app.post("/detect/manual", response_model=DetectionResponse)
async def manual_room_detection(request: ManualDetectionRequest):
    """
    Manually specify room type (for ground truth or fallback).
    
    Set room type manually when automated detection is not available.
    """
    try:
        result = room_detector.manual_room_input(
            room_type=request.room_type,
            room_id=request.room_id,
            building_id=request.building_id
        )
        return detection_result_to_response(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual detection failed: {str(e)}")

@app.get("/detection/history", response_model=DetectionHistoryResponse)
async def get_detection_history(limit: int = 10):
    """
    Get recent detection history.
    
    Returns list of recent room detections with metadata.
    """
    try:
        history = room_detector.get_detection_history(limit)
        detections = [detection_result_to_response(result) for result in history]
        
        return DetectionHistoryResponse(
            detections=detections,
            total_count=len(detections)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@app.get("/detection/statistics", response_model=RoomStatisticsResponse)
async def get_room_statistics():
    """
    Get statistics about detected rooms.
    
    Returns aggregated statistics about room detections.
    """
    try:
        stats = room_detector.get_room_statistics()
        return RoomStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/rooms/types")
async def get_available_room_types():
    """
    Get list of available room types.
    """
    return {
        "room_types": [
            {
                "value": room_type.value,
                "description": room_type.value.replace("_", " ").title()
            }
            for room_type in RoomType
        ]
    }

@app.get("/detection/methods")
async def get_available_detection_methods():
    """
    Get list of available detection methods.
    """
    return {
        "detection_methods": [
            {
                "value": DetectionMethod.COMPUTER_VISION.value,
                "description": "Computer Vision",
                "endpoint": "/detect/image"
            },
            {
                "value": DetectionMethod.MANUAL_INPUT.value,
                "description": "Manual Input",
                "endpoint": "/detect/manual"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "axa-room-detector",
        "detector_initialized": room_detector is not None,
        "total_detections": len(room_detector.detection_history) if room_detector else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port from QR service