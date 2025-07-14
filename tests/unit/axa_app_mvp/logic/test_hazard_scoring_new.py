import pytest
import os
import json
import tempfile
from pathlib import Path
from axa_app_mvp.logic.hazard_scoring import HazardConfig, map_detected_objects_to_hazards, score_hazards

# Sample test data
SAMPLE_CONFIG = {
    "version": "1.0.0",
    "last_updated": "2025-07-14",
    "description": "Test configuration",
    
    "hazards": [
        {
            "id": "loose_rugs",
            "display_name": "Loose Rugs",
            "weights": {
                "mobility": 2,
                "vision": 1,
                "cognition": 1
            },
            "base_score": 10,
            "description": "Rugs that can slip or bunch up"
        },
        {
            "id": "poor_lighting",
            "display_name": "Poor Lighting",
            "weights": {
                "mobility": 1,
                "vision": 2,
                "cognition": 1
            },
            "base_score": 8,
            "description": "Insufficient lighting"
        },
        {
            "id": "steps_or_thresholds",
            "display_name": "Steps/Thresholds",
            "weights": {
                "mobility": 2,
                "vision": 1,
                "cognition": 2
            },
            "base_score": 12,
            "description": "Raised surfaces"
        }
    ],
    
    "detection_mappings": [
        {
            "object": "rug",
            "hazard_id": "loose_rugs",
            "example": "Small throw rug",
            "notes": "Can slip or bunch up"
        },
        {
            "object": "light_bulb_out",
            "hazard_id": "poor_lighting",
            "example": "Burned out bulb",
            "notes": "Poor visibility"
        },
        {
            "object": "threshold",
            "hazard_id": "steps_or_thresholds",
            "example": "Raised threshold",
            "notes": "Difficult for mobility aids"
        }
    ],
    
    "risk_thresholds": [
        {
            "label": "Low",
            "min_score": 0,
            "max_score": 33,
            "color": "green"
        },
        {
            "label": "Medium",
            "min_score": 34,
            "max_score": 66,
            "color": "yellow"
        },
        {
            "label": "High",
            "min_score": 67,
            "max_score": 100,
            "color": "red"
        }
    ]
}

# Fixtures
@pytest.fixture
def temp_config_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(SAMPLE_CONFIG, f)
        f.flush()
        yield f.name
    os.unlink(f.name)

# Tests
def test_hazard_config_initialization(temp_config_file):
    """Test that HazardConfig loads configuration correctly."""
    config = HazardConfig(temp_config_file)
    
    # Check hazards were loaded
    assert len(config.hazards) == 3
    assert "loose_rugs" in config.hazards
    assert config.hazards["loose_rugs"]["display_name"] == "Loose Rugs"
    
    # Check detection mappings
    assert len(config.detection_mapping) == 3
    assert config.detection_mapping["rug"] == "loose_rugs"
    
    # Check risk thresholds
    assert len(config.risk_thresholds) == 3
    assert config.risk_thresholds[0]["label"] == "Low"

def test_get_hazard(temp_config_file):
    """Test retrieving hazard configuration by ID."""
    config = HazardConfig(temp_config_file)
    
    # Test existing hazard
    hazard = config.get_hazard("loose_rugs")
    assert hazard is not None
    assert hazard["display_name"] == "Loose Rugs"
    
    # Test non-existent hazard
    assert config.get_hazard("nonexistent") is None

def test_get_hazard_for_object(temp_config_file):
    """Test retrieving hazard configuration for a detected object."""
    config = HazardConfig(temp_config_file)
    
    # Test existing object
    hazard = config.get_hazard_for_object("rug")
    assert hazard is not None
    assert hazard["id"] == "loose_rugs"
    
    # Test non-existent object
    assert config.get_hazard_for_object("nonexistent") is None

def test_get_risk_level(temp_config_file):
    """Test determining risk level based on score."""
    config = HazardConfig(temp_config_file)
    
    # Test low risk
    assert config.get_risk_level(15)["label"] == "Low"
    assert config.get_risk_level(33)["label"] == "Low"
    
    # Test medium risk
    assert config.get_risk_level(34)["label"] == "Medium"
    assert config.get_risk_level(66)["label"] == "Medium"
    
    # Test high risk
    assert config.get_risk_level(67)["label"] == "High"
    assert config.get_risk_level(100)["label"] == "High"
    
    # Test out of bounds (should return highest risk)
    assert config.get_risk_level(150)["label"] == "High"

def test_map_detected_objects_to_hazards(temp_config_file):
    """Test mapping detected objects to hazard configurations."""
    config = HazardConfig(temp_config_file)
    
    # Test with valid objects
    ai_output = [
        {"object": "rug", "location": "living room"},
        {"object": "light_bulb_out", "location": "hallway"},
        {"object": "threshold", "location": "bathroom"},
        {"object": "unknown_object", "location": "kitchen"}
    ]
    
    hazards = map_detected_objects_to_hazards(ai_output, config)
    
    # Should find 3 hazards (unknown_object is ignored)
    assert len(hazards) == 3
    assert hazards[0]["hazard_id"] == "loose_rugs"
    assert hazards[0]["location"] == "living room"
    assert hazards[1]["hazard_id"] == "poor_lighting"
    assert hazards[2]["hazard_id"] == "steps_or_thresholds"

def test_score_hazards(temp_config_file):
    """Test scoring hazards with a user profile."""
    config = HazardConfig(temp_config_file)
    
    # Test with a user having mobility issues
    profile = {
        "mobility": 1.0,  # High mobility issues
        "vision": 0.0,    # No vision issues
        "cognition": 0.0  # No cognition issues
    }
    
    hazards = [
        {
            "hazard_id": "loose_rugs",
            "hazard_name": "Loose Rugs",
            "location": "living room",
            "object": "rug",
            "base_score": 10,
            "weights": {"mobility": 2, "vision": 1, "cognition": 1}
        },
        {
            "hazard_id": "poor_lighting",
            "hazard_name": "Poor Lighting",
            "location": "hallway",
            "object": "light_bulb_out",
            "base_score": 8,
            "weights": {"mobility": 1, "vision": 2, "cognition": 1}
        }
    ]
    
    result = score_hazards(hazards, profile, config, config.risk_thresholds)
    
    # Check the results
    assert "total_score" in result
    assert "risk_level" in result
    assert "color" in result
    assert "hazard_details" in result
    
    # Should have details for both hazards
    assert len(result["hazard_details"]) == 2
    
    # First hazard (loose_rugs) should have a higher score due to mobility weight
    assert result["hazard_details"][0]["score"] > result["hazard_details"][1]["score"]

def test_score_hazards_no_hazards(temp_config_file):
    """Test scoring with no hazards."""
    config = HazardConfig(temp_config_file)
    profile = {"mobility": 0, "vision": 0, "cognition": 0}
    
    result = score_hazards([], profile, config, config.risk_thresholds)
    
    assert result["total_score"] == 0
    assert result["risk_level"] == "None"
    assert result["color"] == "green"
    assert len(result["hazard_details"]) == 0
