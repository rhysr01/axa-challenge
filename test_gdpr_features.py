#!/usr/bin/env python3
"""
Test script for AXA QR MVP GDPR compliance features.

This script demonstrates:
1. Consent checking
2. QR code generation with audit logging
3. Data export functionality
4. Error handling for users without consent
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
API_BASE = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Helper function to test API endpoints."""
    url = f"{API_BASE}{endpoint}"
    
    print(f"\n🔍 Testing: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"   Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"   Response: {response.text[:200]}...")
            return {"status_code": response.status_code, "text": response.text}
            
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Cannot connect to API. Make sure the server is running!")
        return {"error": "connection_failed"}
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return {"error": str(e)}

def main():
    """Test GDPR compliance features."""
    
    print("🎯 AXA QR MVP - GDPR Compliance Testing")
    print("=" * 50)
    
    # Test 1: Health check with GDPR status
    print("\n1️⃣ Health Check with GDPR Status")
    health = test_endpoint("GET", "/health")
    
    # Test 2: Check consent for pilot user (should have consent)
    print("\n2️⃣ Check Consent for Pilot User")
    pilot_user = "user_12345"
    consent_status = test_endpoint("GET", f"/consent-status/{pilot_user}")
    
    # Test 3: Try QR generation for pilot user (should succeed)
    print("\n3️⃣ Generate QR for User with Consent")
    qr_request = {
        "user_id": pilot_user,
        "axa_id_url": f"https://axa.com/profile/{pilot_user}",
        "contact": {
            "name": "John Pilot",
            "email": "john.pilot@axa.com",
            "phone": "+33123456789"
        },
        "output_format": "png"
    }
    qr_result = test_endpoint("POST", "/generate", qr_request)
    
    # Test 4: Try QR generation for user without consent (should fail)
    print("\n4️⃣ Generate QR for User WITHOUT Consent")
    no_consent_user = "unauthorized_user_999"
    qr_request_fail = {
        "user_id": no_consent_user,
        "axa_id_url": f"https://axa.com/profile/{no_consent_user}",
        "contact": {
            "name": "No Consent User", 
            "email": "no.consent@example.com"
        }
    }
    qr_fail_result = test_endpoint("POST", "/generate", qr_request_fail)
    
    # Test 5: Grant consent to new user
    print("\n5️⃣ Grant Consent to New User")
    grant_result = test_endpoint("POST", f"/admin/grant-consent/{no_consent_user}")
    
    # Test 6: Try QR generation again (should now succeed)
    print("\n6️⃣ Generate QR After Granting Consent")
    qr_success_result = test_endpoint("POST", "/generate", qr_request_fail)
    
    # Test 7: Export user data (GDPR data portability)
    print("\n7️⃣ Export User Data (GDPR Data Portability)")
    export_result = test_endpoint("GET", f"/export-data/{pilot_user}")
    
    # Test 8: List all consented users
    print("\n8️⃣ List All Consented Users")
    consented_users = test_endpoint("GET", "/admin/consented-users")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 GDPR Compliance Test Summary")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 8
    
    if health and health.get("gdpr_compliance") == "enabled":
        print("✅ Health check shows GDPR compliance enabled")
        tests_passed += 1
    else:
        print("❌ Health check missing GDPR compliance")
    
    if consent_status and consent_status.get("has_consent"):
        print("✅ Consent checking works for pilot users")
        tests_passed += 1
    else:
        print("❌ Consent checking failed")
    
    if qr_result and qr_result.get("success") and qr_result.get("consent_verified"):
        print("✅ QR generation with consent works")
        tests_passed += 1
    else:
        print("❌ QR generation with consent failed")
    
    if qr_fail_result and qr_fail_result.get("status_code") == 403:
        print("✅ QR generation properly blocks users without consent")
        tests_passed += 1
    else:
        print("❌ Consent blocking not working")
    
    if grant_result and grant_result.get("has_consent"):
        print("✅ Consent granting works")
        tests_passed += 1
    else:
        print("❌ Consent granting failed")
    
    if qr_success_result and qr_success_result.get("success"):
        print("✅ QR generation works after consent granted")
        tests_passed += 1
    else:
        print("❌ QR generation after consent failed")
    
    if export_result and export_result.get("user_id") == pilot_user:
        print("✅ Data export (GDPR portability) works")
        tests_passed += 1
    else:
        print("❌ Data export failed")
    
    if consented_users and len(consented_users.get("consented_users", [])) >= 2:
        print("✅ Consented users listing works")
        tests_passed += 1
    else:
        print("❌ Consented users listing failed")
    
    print(f"\n🎯 Score: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All GDPR compliance features working correctly!")
        print("\n📋 Next steps:")
        print("   • Check regulatory_audit.log for audit trail")
        print("   • Test n8n workflow with consent checking")
        print("   • Deploy to staging environment")
    else:
        print("⚠️  Some tests failed - check the API server logs")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure the FastAPI server is running: cd qr && python app.py")
        print("   • Check that all dependencies are installed")
        print("   • Verify regulatory_audit.log is being created")

if __name__ == "__main__":
    main()