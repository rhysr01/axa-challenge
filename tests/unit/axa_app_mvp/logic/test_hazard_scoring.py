import pytest
import os
import tempfile
from pathlib import Path
from axa_app_mvp.logic.hazard_scoring import (
    load_risk_matrix,
    load_thresholds,
    load_detection_mapping,
    map_detected_objects_to_hazards,
    score_hazards
)

# Sample test data
SAMPLE_RISK_MATRIX = """hazard,weight_mobility,weight_vision,weight_cognition,base_score
loose_rugs,2,1,1,10
poor_lighting,1,2,1,8
steps_or_thresholds,2,1,2,12
"""

SAMPLE_THRESHOLDS = """label,min_score,max_score,color
Low,0,33,green
Medium,34,66,yellow
High,67,100,red
"""

SAMPLE_MAPPING = """object,hazard,example,notes
rug,loose_rugs,Small throw rug,Can slip or bunch up
light_bulb_out,poor_lighting,Burned out bulb,Poor visibility
threshold,steps_or_thresholds,Raised threshold,Difficult for mobility aids
"""

# Fixtures
@pytest.fixture
def temp_risk_matrix():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(SAMPLE_RISK_MATRIX)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_thresholds():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(SAMPLE_THRESHOLDS)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_mapping():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(SAMPLE_MAPPING)
        f.flush()
        yield f.name
    os.unlink(f.name)

def test_load_risk_matrix(temp_risk_matrix):
    """Test loading the risk matrix from a CSV file."""
    matrix = load_risk_matrix(temp_risk_matrix)
    
    assert 'loose_rugs' in matrix
    assert matrix['loose_rugs']['base_score'] == 10
    assert matrix['loose_rugs']['mobility_weight'] == 2
    assert matrix['poor_lighting']['vision_weight'] == 2

def test_load_thresholds(temp_thresholds):
    """Test loading risk thresholds from a CSV file."""
    thresholds = load_thresholds(temp_thresholds)
    
    assert len(thresholds) == 3
    assert thresholds[0]['label'] == 'Low'
    assert thresholds[0]['min'] == 0
    assert thresholds[0]['max'] == 33
    assert thresholds[0]['color'] == 'green'

def test_load_detection_mapping(temp_mapping):
    """Test loading the object to hazard mapping."""
    mapping = load_detection_mapping(temp_mapping)
    
    assert mapping['rug'] == 'loose_rugs'
    assert mapping['light_bulb_out'] == 'poor_lighting'
    assert mapping['threshold'] == 'steps_or_thresholds'

def test_map_detected_objects_to_hazards():
    """Test mapping detected objects to hazard types."""
    mapping = {
        'rug': 'loose_rugs',
        'light_bulb_out': 'poor_lighting'
    }
    
    detected_objects = [
        {'object': 'rug', 'location': {'x': 100, 'y': 200}, 'confidence': 0.95},
        {'object': 'light_bulb_out', 'location': {'x': 50, 'y': 300}, 'confidence': 0.85},
        {'object': 'unknown', 'location': {'x': 200, 'y': 100}, 'confidence': 0.5}
    ]
    
    hazards = map_detected_objects_to_hazards(detected_objects, mapping)
    
    assert len(hazards) == 2
    assert hazards[0]['hazard'] == 'loose_rugs'
    assert hazards[0]['object'] == 'rug'
    assert hazards[0]['location'] == {'x': 100, 'y': 200}
    
    assert hazards[1]['hazard'] == 'poor_lighting'
    assert hazards[1]['object'] == 'light_bulb_out'
    assert hazards[1]['location'] == {'x': 50, 'y': 300}

def test_score_hazards():
    """Test scoring hazards based on user profile."""
    # Test data - using dictionaries instead of Hazard class
    hazards = [
        {'hazard': 'loose_rugs', 'object': 'rug', 'location': {'x': 100, 'y': 200}},
        {'hazard': 'poor_lighting', 'object': 'light_bulb_out', 'location': {'x': 50, 'y': 300}}
    ]
    
    profile = {
        'mobility': True,
        'vision': False,
        'cognition': True,
        'age': 75
    }
    
    risk_matrix = {
        'loose_rugs': {
            'base_score': 10,
            'mobility_weight': 2,
            'vision_weight': 1,
            'cognition_weight': 1
        },
        'poor_lighting': {
            'base_score': 8,
            'mobility_weight': 1,
            'vision_weight': 2,
            'cognition_weight': 1
        }
    }
    
    thresholds = [
        {'label': 'Low', 'min': 0, 'max': 33, 'color': 'green'},
        {'label': 'Medium', 'min': 34, 'max': 66, 'color': 'yellow'},
        {'label': 'High', 'min': 67, 'max': 100, 'color': 'red'}
    ]
    
    # Test with mobility impairment
    result = score_hazards(hazards, profile, risk_matrix, thresholds)
    
    # Verify results
    assert 'score' in result
    assert 'riskLevel' in result
    assert 'hazards' in result
    assert len(result['hazards']) == 2
    assert 'recommendation' in result
    
    # Verify hazard details - the actual implementation returns objects with base_score and final_score
    for hazard in result['hazards']:
        assert 'base_score' in hazard
        assert 'final_score' in hazard
        assert 'object' in hazard
        assert 'location' in hazard
    
    # Test with no impairments
    profile_no_impairments = {'mobility': False, 'vision': False, 'cognition': False, 'age': 40}
    result = score_hazards(hazards, profile_no_impairments, risk_matrix, thresholds)
    assert 'score' in result
    assert 'riskLevel' in result
    assert 'hazards' in result
    assert len(result['hazards']) == 2
    assert 'recommendation' in result

def test_score_hazards_no_hazards():
    """Test scoring with no hazards."""
    result = score_hazards([], {}, {}, [])
    assert result['score'] == 0
    assert 'riskLevel' in result
    assert result['hazards'] == []
    assert 'recommendation' in result
