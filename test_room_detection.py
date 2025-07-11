#!/usr/bin/env python3
"""
Test script for AXA Room Detection functionality.

This script demonstrates:
1. Image-based room detection
2. Sensor-based room detection  
3. Manual room input
4. Detection history and statistics
5. API endpoint testing
"""

import requests
import json
import os
import tempfile
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import io

# API base URL for room detection service
ROOM_API_BASE = "http://localhost:8001"

def create_test_image(room_type: str) -> str:
    """Create a test image with room type label for testing."""
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add room type text to image
    try:
        # Try to use a default font, fallback to basic if not available
        font = ImageFont.load_default()
    except:
        font = None
    
    text = f"Test {room_type.replace('_', ' ').title()} Image"
    draw.text((50, 200), text, fill='black', font=font)
    
    # Add some mock room elements based on type
    if "office" in room_type:
        # Draw desk and chair representation
        draw.rectangle([100, 300, 200, 350], fill='brown')  # desk
        draw.rectangle([150, 350, 180, 400], fill='gray')   # chair
    elif "meeting" in room_type:
        # Draw table and chairs
        draw.rectangle([200, 250, 400, 300], fill='brown')  # table
        for i in range(4):
            x = 180 + i * 60
            draw.rectangle([x, 230, x+20, 250], fill='gray')  # chairs
    elif "kitchen" in room_type:
        # Draw counter and appliances
        draw.rectangle([50, 350, 300, 400], fill='gray')   # counter
        draw.rectangle([320, 320, 370, 400], fill='silver') # fridge
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{room_type}.jpg')
    img.save(temp_file.name, 'JPEG')
    return temp_file.name

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] | None = None, files: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Helper function to test API endpoints."""
    url = f"{ROOM_API_BASE}{endpoint}"
    
    print(f"\n🔍 Testing: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
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
        print("   ❌ ERROR: Cannot connect to Room Detection API. Make sure the server is running on port 8001!")
        return {"error": "connection_failed"}
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return {"error": str(e)}

def main():
    """Test room detection functionality."""
    
    print("🏢 AXA Room Detection - Functionality Testing")
    print("=" * 55)
    
    # Test 1: Health check
    print("\n1️⃣ Health Check")
    health = test_endpoint("GET", "/health")
    
    # Test 2: Get available room types
    print("\n2️⃣ Available Room Types")
    room_types = test_endpoint("GET", "/rooms/types")
    
    # Test 3: Get available detection methods
    print("\n3️⃣ Available Detection Methods")
    methods = test_endpoint("GET", "/detection/methods")
    
    # Test 4: Image-based detection
    print("\n4️⃣ Image-Based Room Detection")
    
    # Create test images for different room types
    test_rooms = ["office", "meeting_room", "kitchen"]
    image_results = []
    
    for room_type in test_rooms:
        print(f"\n   📸 Testing {room_type} image detection...")
        
        # Create test image
        image_path = create_test_image(room_type)
        
        try:
            # Test image upload
            with open(image_path, 'rb') as f:
                files = {'file': (f'{room_type}.jpg', f, 'image/jpeg')}
                result = test_endpoint("POST", "/detect/image", files=files)
                image_results.append(result)
        finally:
            # Clean up test image
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    # Test 5: Manual room detection
    print("\n5️⃣ Manual Room Detection")
    manual_cases = [
        {
            "room_type": "office",
            "room_id": "OFF-A-101",
            "building_id": "AXA-HQ-Paris"
        },
        {
            "room_type": "meeting_room",
            "room_id": "MR-B-205",
            "building_id": "AXA-HQ-Lyon"
        }
    ]
    
    manual_results = []
    for case in manual_cases:
        result = test_endpoint("POST", "/detect/manual", case)
        manual_results.append(result)
    
    # Test 6: Detection history
    print("\n6️⃣ Detection History")
    history = test_endpoint("GET", "/detection/history?limit=5")
    
    # Test 7: Room statistics
    print("\n7️⃣ Room Statistics")
    statistics = test_endpoint("GET", "/detection/statistics")
    
    # Summary
    print("\n" + "=" * 55)
    print("📊 Room Detection Test Summary")
    print("=" * 55)
    
    tests_passed = 0
    total_tests = 7
    
    if health and health.get("status") == "healthy":
        print("✅ Health check passed")
        tests_passed += 1
    else:
        print("❌ Health check failed")
    
    if room_types and "room_types" in room_types:
        print("✅ Room types endpoint working")
        tests_passed += 1
    else:
        print("❌ Room types endpoint failed")
    
    if methods and "detection_methods" in methods:
        print("✅ Detection methods endpoint working")
        tests_passed += 1
    else:
        print("❌ Detection methods endpoint failed")
    
    successful_image_detections = sum(1 for r in image_results if r and r.get("room_type"))
    if successful_image_detections >= 2:
        print(f"✅ Image detection working ({successful_image_detections}/3 successful)")
        tests_passed += 1
    else:
        print(f"❌ Image detection issues ({successful_image_detections}/3 successful)")
    
    successful_manual_detections = sum(1 for r in manual_results if r and r.get("room_type"))
    if successful_manual_detections >= 1:
        print(f"✅ Manual detection working ({successful_manual_detections}/2 successful)")
        tests_passed += 1
    else:
        print(f"❌ Manual detection issues ({successful_manual_detections}/2 successful)")
    
    if history and history.get("detections"):
        print("✅ Detection history working")
        tests_passed += 1
    else:
        print("❌ Detection history failed")
    
    if statistics and statistics.get("total_detections", 0) > 0:
        print("✅ Statistics generation working")
        tests_passed += 1
    else:
        print("❌ Statistics generation failed")
    
    print(f"\n🎯 Score: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 5:
        print("🎉 Room detection system is working well!")
        print("\n📋 Next steps:")
        print("   • Integrate with computer vision models for better image detection")
        print("   • Train ML models on your specific room types")
        print("   • Add more sophisticated image analysis features")
        print("   • Implement room layout detection")
    else:
        print("⚠️  Several tests failed - check the API server")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure the room detection server is running: cd adapt && python3 app.py")
        print("   • Check that all dependencies are installed")
        print("   • Verify the server is accessible on port 8001")
    
    # Show some detection insights
    if statistics and "room_type_distribution" in statistics:
        print(f"\n📈 Detection Insights:")
        print(f"   • Total detections: {statistics.get('total_detections', 0)}")
        print(f"   • Most common room: {statistics.get('most_common_room', 'N/A')}")
        print(f"   • Average confidence: {statistics.get('average_confidence', 0):.2f}")
        
        room_dist = statistics.get("room_type_distribution", {})
        if room_dist:
            print(f"   • Room type distribution:")
            for room_type, count in room_dist.items():
                print(f"     - {room_type}: {count}")

if __name__ == "__main__":
    main()