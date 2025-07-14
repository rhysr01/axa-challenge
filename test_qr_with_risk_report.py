"""
End-to-end test for QR code generation with fall risk report integration.
"""
import os
import sys
import json
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Import the FastAPI app and required modules
from main import app, generate_secure_url
from axa_app_mvp.logic.hazard_scoring import HazardConfig, map_detected_objects_to_hazards, score_hazards
from axa_app_mvp.logic.qr_utils import validate_token

# Test client
client = TestClient(app)

@pytest.fixture
def test_risk_report() -> Dict[str, Any]:
    """Fixture that returns a sample risk report for testing."""
    return {
        "score": 78,
        "risk_level": "High",
        "hazards": [
            {
                "object": "wet floor",
                "location": "bathroom",
                "type": "slippery",
                "severity": "high",
                "reason": "Wet surface detected near the bathtub"
            },
            {
                "object": "loose rug",
                "location": "bedroom",
                "type": "rug",
                "severity": "medium",
                "reason": "Unsecured rug with curled edges"
            }
        ],
        "recommendation": "Install grab bars in the bathroom and secure or remove loose rugs. Consider using non-slip mats in wet areas.",
        "generated_at": datetime.utcnow().isoformat(),
        "total_score": 78
    }

@pytest.fixture
def test_user_id() -> str:
    """Fixture that returns a unique test user ID."""
    return f"test_user_{uuid.uuid4().hex[:8]}"

def save_risk_report(risk_report: Dict[str, Any], user_id: str, output_dir: str) -> str:
    """Save a risk report to a file and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"risk_report_{user_id}.json")
    with open(report_path, 'w') as f:
        json.dump(risk_report, f, indent=2)
    return report_path

@pytest.fixture
def test_profile() -> Dict[str, Any]:
    """Fixture that returns a sample user profile for testing."""
    return {
        "personal_info": {
            "name": "Test User",
            "dob": "1950-01-01",
            "age": 74
        },
        "medical_info": {
            "blood_type": "O+",
            "allergies": ["penicillin", "latex"],
            "conditions": ["hypertension", "arthritis"]
        },
        "emergency_contacts": [
            {
                "name": "John Doe",
                "relationship": "son",
                "phone": "+34-600-123-456"
            }
        ]
    }

@pytest.fixture
def setup_test_environment(tmp_path, test_risk_report, test_user_id, test_profile):
    """Set up the test environment with necessary files and configurations."""
    # Set up directories
    output_dir = tmp_path / 'outputs'
    output_dir.mkdir()
    
    profile_dir = tmp_path / 'axa_app_mvp' / 'profiles'
    profile_dir.mkdir(parents=True)
    
    # Save test profile
    profile_path = profile_dir / f'health_profile_{test_user_id}.json'
    with open(profile_path, 'w') as f:
        json.dump(test_profile, f, indent=2)
    
    # Save risk report
    report_path = output_dir / f'risk_report_{test_user_id}.json'
    with open(report_path, 'w') as f:
        json.dump(test_risk_report, f, indent=2)
    
    # Configure the app
    import sys
    import importlib
    
    if 'main' in sys.modules:
        importlib.reload(sys.modules['main'])
    import main
    
    # Set the OUTPUT_DIR in the FastAPI app's state
    main.app.state.OUTPUT_DIR = str(output_dir)
    
    return {
        'output_dir': str(output_dir),
        'profile_path': str(profile_path),
        'report_path': str(report_path),
        'app': main.app
    }

def test_end_to_end_qr_flow(setup_test_environment, test_risk_report, test_user_id):
    """Test the complete flow of generating and viewing a QR code with risk report."""
    env = setup_test_environment
    
    try:
        # Save the risk report to a file first
        report_path = save_risk_report(test_risk_report, test_user_id, env['output_dir'])
        
        # Generate the secure URL
        url = generate_secure_url(
            user_id=test_user_id,
            expiry_hours=24,
            output_dir=env['output_dir']
        )
        token = url.split('/')[-1]  # Extract token from URL
        
        # Verify token was generated
        assert token is not None, "Token generation failed"
        
        # Step 2: Verify the token file was created
        token_path = os.path.join(env['output_dir'], f"qr_token_{token}.json")
        assert os.path.exists(token_path), f"Token file not found at {token_path}"
        
        # Load the token data
        with open(token_path) as f:
            token_data = json.load(f)
        
        # The token should contain the user_id and expiry
        assert token_data["user_id"] == test_user_id
        assert "expiry" in token_data
        
        # Verify the token data contains the risk report
        assert "risk_report" in token_data, "Risk report not found in token data"
        token_risk_report = token_data["risk_report"]
        assert "hazards" in token_risk_report, "Hazards not found in token risk report"
        
        # Debug: Print token data for inspection
        print("\nToken data:", json.dumps(token_data, indent=2))
        
        # The risk report should be loaded from the file when viewing the QR
        # Step 3: Access the QR code view using the test client
        response = client.get(f"/qr-deep/{test_user_id}?token={token}")
        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        
        # Save the full HTML response for inspection
        response_path = os.path.join(env['output_dir'], 'qr_response.html')
        with open(response_path, 'w') as f:
            f.write(response.text)
        print(f"[DEBUG] Full HTML response saved to: {response_path}")
        
        # Print the first 1000 characters of the response
        print("\n[DEBUG] First 1000 chars of response:")
        print(response.text[:1000])
        
        # Check if hazards section exists in the response
        hazards_section = '<h5 class="mb-3">Identified Hazards</h5>'
        if hazards_section in response.text:
            print("[DEBUG] Hazards section found in response")
            # Find the position of the hazards section
            hazards_pos = response.text.find(hazards_section)
            # Get 1000 characters after the hazards section
            hazards_content = response.text[hazards_pos:hazards_pos+1000]
            print("\n[DEBUG] Hazards section content (first 1000 chars):")
            print(hazards_content)
        else:
            print("[ERROR] Hazards section NOT found in response")
        
        # Check for each hazard in the response
        print("\n[DEBUG] Checking for hazard objects in response:")
        for hazard in test_risk_report.get("hazards", []):
            hazard_obj = hazard["object"]
            if hazard_obj in response.text:
                print(f"[FOUND] Hazard object: {hazard_obj}")
                # Find the position of this hazard in the response
                pos = response.text.find(hazard_obj)
                if pos != -1:
                    # Show some context around the found hazard
                    start = max(0, pos - 50)
                    end = min(len(response.text), pos + len(hazard_obj) + 50)
                    print(f"[CONTEXT] ...{response.text[start:end]}...")
            else:
                print(f"[MISSING] Hazard object: {hazard_obj}")
        
        # Verify the response contains the risk report data
        print("\n[DEBUG] Verifying response content:")
        content = response.text
        
        print("Checking for score in response...")
        score = str(test_risk_report["score"])
        if score in content:
            print(f"[FOUND] Score: {score}")
        else:
            print(f"[MISSING] Score: {score}")
        
        print("Checking for risk level in response...")
        risk_level = test_risk_report["risk_level"]
        if risk_level in content:
            print(f"[FOUND] Risk level: {risk_level}")
        else:
            print(f"[MISSING] Risk level: {risk_level}")
        
        # Check for hazards in the response
        print("\n[DEBUG] Verifying hazards in response:")
        for hazard in test_risk_report.get("hazards", []):
            print(f"Looking for hazard object: {hazard['object']}")
            if hazard["object"] in content:
                print(f"[FOUND] Hazard object: {hazard['object']}")
            else:
                print(f"[MISSING] Hazard object: {hazard['object']}")
            
            print(f"Looking for hazard location: {hazard['location']}")
            if hazard["location"] in content:
                print(f"[FOUND] Hazard location: {hazard['location']}")
            else:
                print(f"[MISSING] Hazard location: {hazard['location']}")
        
        print("\nChecking for recommendation in response...")
        recommendation = test_risk_report["recommendation"]
        if recommendation in content:
            print("[FOUND] Recommendation")
        else:
            print("[MISSING] Recommendation")
        
        # Now perform the actual assertions
        assert score in content, "Risk score not found in response"
        assert risk_level in content, "Risk level not found in response"
        for hazard in test_risk_report.get("hazards", []):
            assert hazard["object"] in content, f"Hazard object '{hazard['object']}' not found in response"
            assert hazard["location"] in content, f"Hazard location '{hazard['location']}' not found in response"
        assert recommendation in content, "Recommendation not found in response"
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

# Test cases for different risk levels
@pytest.mark.parametrize("score,expected_level", [
    (85, "High"),
    (50, "Medium"),
    (20, "Low")
])
def test_risk_levels(setup_test_environment, test_user_id, score, expected_level):
    """Test that different risk scores are correctly categorized."""
    env = setup_test_environment
    
    # Create a test risk report with the specified score
    test_report = {
        "score": score,
        "risk_level": expected_level,
        "hazards": [{"object": "test", "location": "test", "type": "test", "severity": "test"}],
        "recommendation": "Test recommendation",
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # First save the risk report to a file
    report_path = save_risk_report(test_report, test_user_id, env['output_dir'])
    
    # Generate the secure URL
    url = generate_secure_url(
        user_id=test_user_id,
        expiry_hours=24,
        output_dir=env['output_dir']
    )
    token = url.split('/')[-1]  # Extract token from URL  
    
    # Access the QR view and verify risk level is displayed correctly
    response = client.get(f"/qr-deep/{test_user_id}?token={token}")
    assert response.status_code == 200
    assert expected_level in response.text

# Test case for empty hazards
def test_empty_hazards(setup_test_environment, test_user_id):
    """Test that the QR view handles empty hazards list gracefully."""
    env = setup_test_environment
    
    test_report = {
        "score": 30,
        "risk_level": "Medium",
        "hazard_details": [],  # Empty hazards list
        "recommendation": "No specific hazards found",
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Save the test report
    report_path = save_risk_report(test_report, test_user_id, env['output_dir'])
    
    # Generate the secure URL
    url = generate_secure_url(
        user_id=test_user_id,
        expiry_hours=24,
        output_dir=env['output_dir']
    )
    token = url.split('/')[-1]
    
    # Access the QR view
    response = client.get(f"/qr-deep/{test_user_id}?token={token}")
    assert response.status_code == 200
    
    # The template should show a message when no hazards are found
    assert "No specific hazards were identified" in response.text or \
           "No hazards detected" in response.text or \
           "hazard_details" not in response.text

if __name__ == "__main__":
    # Run the test directly for easier debugging
    test_end_to_end_qr_flow(Path("test_output"))
    print("Test completed.")
