"""
Room Detection Module for AXA Adapt Component

This module provides room detection capabilities:
- Computer vision-based room type detection from images
- Manual room type classification for ground truth data
- Detection history and analytics
- Confidence scoring for classification results
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

class RoomType(Enum):
    """Detected room types."""
    OFFICE = "office"
    MEETING_ROOM = "meeting_room"
    CONFERENCE_ROOM = "conference_room"
    LOBBY = "lobby"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    STORAGE = "storage"
    CORRIDOR = "corridor"
    UNKNOWN = "unknown"

class DetectionMethod(Enum):
    """Available detection methods."""
    COMPUTER_VISION = "computer_vision"
    MANUAL_INPUT = "manual_input"

@dataclass
class DetectionResult:
    """Result of room detection analysis."""
    room_type: RoomType
    confidence: float  # 0.0 to 1.0
    detection_method: DetectionMethod
    timestamp: str
    metadata: Dict[str, Any]
    room_id: Optional[str] = None
    building_id: Optional[str] = None

@dataclass
class RoomFeatures:
    """Detected room features and characteristics."""
    size_estimate: Optional[str] = None  # "small", "medium", "large"
    occupancy_count: Optional[int] = None
    lighting_level: Optional[str] = None  # "bright", "dim", "dark"
    noise_level: Optional[str] = None    # "quiet", "moderate", "loud"
    furniture_detected: List[str] = None
    equipment_detected: List[str] = None
    
    def __post_init__(self):
        if self.furniture_detected is None:
            self.furniture_detected = []
        if self.equipment_detected is None:
            self.equipment_detected = []

class RoomDetector:
    """Main room detection class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.detection_history: List[DetectionResult] = []
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for room detection."""
        logger = logging.getLogger("room_detector")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def detect_room_from_image(self, image_path: str) -> DetectionResult:
        """
        Detect room type from image using computer vision.
        
        Args:
            image_path: Path to image file
            
        Returns:
            DetectionResult with room analysis
        """
        self.logger.info(f"Analyzing image: {image_path}")
        
        # Placeholder for computer vision implementation
        # In real implementation, this would use ML models like:
        # - ResNet/VGG for image classification
        # - YOLO for object detection
        # - Custom trained models for room types
        
        if not os.path.exists(image_path):
            return DetectionResult(
                room_type=RoomType.UNKNOWN,
                confidence=0.0,
                detection_method=DetectionMethod.COMPUTER_VISION,
                timestamp=datetime.now().isoformat(),
                metadata={"error": "Image file not found", "image_path": image_path}
            )
        
        # Mock detection based on filename (for demo purposes)
        filename = os.path.basename(image_path).lower()
        
        detection_mapping = {
            "office": (RoomType.OFFICE, 0.85),
            "meeting": (RoomType.MEETING_ROOM, 0.90),
            "conference": (RoomType.CONFERENCE_ROOM, 0.88),
            "lobby": (RoomType.LOBBY, 0.92),
            "kitchen": (RoomType.KITCHEN, 0.87),
            "bathroom": (RoomType.BATHROOM, 0.95),
            "storage": (RoomType.STORAGE, 0.80),
            "corridor": (RoomType.CORRIDOR, 0.85)
        }
        
        detected_type = RoomType.UNKNOWN
        confidence = 0.3
        
        for keyword, (room_type, conf) in detection_mapping.items():
            if keyword in filename:
                detected_type = room_type
                confidence = conf
                break
        
        result = DetectionResult(
            room_type=detected_type,
            confidence=confidence,
            detection_method=DetectionMethod.COMPUTER_VISION,
            timestamp=datetime.now().isoformat(),
            metadata={
                "image_path": image_path,
                "filename": filename,
                "analysis_method": "filename_based_demo"
            }
        )
        
        self.detection_history.append(result)
        return result



    def manual_room_input(self, room_type: str, room_id: Optional[str] = None, building_id: Optional[str] = None) -> DetectionResult:
        """
        Manually specify room type (for ground truth or fallback).
        
        Args:
            room_type: Room type string
            room_id: Optional room identifier
            building_id: Optional building identifier
            
        Returns:
            DetectionResult with manual input
        """
        try:
            detected_type = RoomType(room_type.lower())
        except ValueError:
            detected_type = RoomType.UNKNOWN
        
        result = DetectionResult(
            room_type=detected_type,
            confidence=1.0,
            detection_method=DetectionMethod.MANUAL_INPUT,
            timestamp=datetime.now().isoformat(),
            metadata={"manual_input": True},
            room_id=room_id,
            building_id=building_id
        )
        
        self.detection_history.append(result)
        return result

    def get_detection_history(self, limit: int = 10) -> List[DetectionResult]:
        """Get recent detection history."""
        return self.detection_history[-limit:]

    def get_room_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected rooms."""
        if not self.detection_history:
            return {"total_detections": 0}
        
        room_counts = {}
        method_counts = {}
        confidence_sum = 0
        
        for result in self.detection_history:
            room_type = result.room_type.value
            method = result.detection_method.value
            
            room_counts[room_type] = room_counts.get(room_type, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
            confidence_sum += result.confidence
        
        return {
            "total_detections": len(self.detection_history),
            "room_type_distribution": room_counts,
            "detection_method_distribution": method_counts,
            "average_confidence": confidence_sum / len(self.detection_history),
            "most_common_room": max(room_counts.items(), key=lambda x: x[1])[0] if room_counts else None
        }