import pytest
import json
import tempfile
import os
from pathlib import Path
from axa_app_mvp.logic.hazard_scoring import (
    HazardConfig,
    map_detected_objects_to_hazards,
    score_hazards
)

# Sample test config
SAMPLE_CONFIG = {
    "version": "1.0.0",
    "last_updated": "2025-01-01",
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
            "description": "Rugs that can slip or bunch up, creating a trip hazard"
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
            "description": "Insufficient lighting that reduces visibility"
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
            "description": "Raised thresholds or steps that are difficult to see"
        }
    ],
    "detection_mappings": [
        {
            "object": "rug",
            "hazard_id": "loose_rugs",
            "example": "Small throw rug in bedroom",
            "notes": "Can slip or bunch up"
        },
        {
            "object": "light_bulb_out",
            "hazard_id": "poor_lighting",
            "example": "Burned out bulb in hallway",
            "notes": "Reduces visibility"
        },
        {
            "object": "threshold",
            "hazard_id": "steps_or_thresholds",
            "example": "Raised threshold between rooms",
            "notes": "Difficult to see and navigate"
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

@pytest.fixture
def hazard_config(temp_config_file):
    return HazardConfig(temp_config_file)

def test_hazard_config_loading(hazard_config):
    """Test loading the hazard configuration from JSON."""
    # Test hazard loading
    assert 'loose_rugs' in hazard_config.hazards
    assert hazard_config.hazards['loose_rugs']['base_score'] == 10
    assert hazard_config.hazards['loose_rugs']['weights']['mobility'] == 2
    
    # Test detection mapping
    assert hazard_config.detection_mapping['rug'] == 'loose_rugs'
    assert hazard_config.detection_mapping['light_bulb_out'] == 'poor_lighting'
    
    # Test risk thresholds
    assert len(hazard_config.risk_thresholds) == 3
    assert hazard_config.risk_thresholds[0]['label'] == 'Low'
    assert hazard_config.risk_thresholds[0]['min_score'] == 0
    assert hazard_config.risk_thresholds[0]['max_score'] == 33

def test_map_detected_objects_to_hazards(hazard_config):
    """Test mapping detected objects to hazard types using HazardConfig."""
    detected_objects = [
        {'object': 'rug', 'location': {'x': 100, 'y': 200}, 'confidence': 0.95},
        {'object': 'light_bulb_out', 'location': {'x': 50, 'y': 300}, 'confidence': 0.85},
        {'object': 'unknown', 'location': {'x': 200, 'y': 100}, 'confidence': 0.5}
    ]
    
    hazards = map_detected_objects_to_hazards(detected_objects, hazard_config)
    
    assert len(hazards) == 2
    assert hazards[0]['hazard_id'] == 'loose_rugs'
    assert hazards[0]['hazard_name'] == 'Loose Rugs'
    assert hazards[0]['object'] == 'rug'
    assert hazards[0]['location'] == {'x': 100, 'y': 200}
    assert hazards[0]['base_score'] == 10
    
    assert hazards[1]['hazard_id'] == 'poor_lighting'
    assert hazards[1]['hazard_name'] == 'Poor Lighting'
    assert hazards[1]['object'] == 'light_bulb_out'
    assert hazards[1]['location'] == {'x': 50, 'y': 300}
    assert hazards[1]['base_score'] == 8

def test_score_hazards(hazard_config):
    """Test scoring hazards based on user profile using HazardConfig."""
    # Create test hazards using the map_detected_objects_to_hazards function
    detected_objects = [
        {'object': 'rug', 'location': {'x': 100, 'y': 200}, 'confidence': 0.95},
        {'object': 'light_bulb_out', 'location': {'x': 50, 'y': 300}, 'confidence': 0.85}
    ]
    hazards = map_detected_objects_to_hazards(detected_objects, hazard_config)
    
    # Test with mobility and cognition impairments
    profile = {
        'mobility': 0.8,  # 80% impairment
        'vision': 0.0,    # No impairment
        'cognition': 0.5, # 50% impairment
        'age': 75
    }
    
    # Test scoring
    result = score_hazards(hazards, profile, hazard_config, hazard_config.risk_thresholds)
    
    # Verify results
    assert 'total_score' in result
    assert 'risk_level' in result
    assert 'hazard_details' in result
    assert 'recommendation' in result
    assert len(result['hazard_details']) == 2
    
    # Verify hazard details
    for hazard in result['hazard_details']:
        assert 'hazard_id' in hazard
        assert 'hazard_name' in hazard
        assert 'object' in hazard
        assert 'location' in hazard
        assert 'score' in hazard
        assert 'base_score' in hazard
        assert 'weights' in hazard
    
    # Test with no impairments
    profile_no_impairments = {
        'mobility': 0.0,
        'vision': 0.0,
        'cognition': 0.0,
        'age': 40
    }
    result = score_hazards(hazards, profile_no_impairments, hazard_config, hazard_config.risk_thresholds)
    
    # Scores should be lower with no impairments
    assert result['total_score'] < 50  # Arbitrary check that score is reasonable

def test_score_hazards_no_hazards(hazard_config):
    """Test scoring with no hazards."""
    result = score_hazards([], {}, hazard_config, hazard_config.risk_thresholds)
    assert result['total_score'] == 0
    assert result['risk_level'] == 'None'
    assert result['hazard_details'] == []
    assert 'recommendation' in result
