#!/usr/bin/env python3
import json
import qrcode
import uuid
import sys
from datetime import datetime, timedelta

def generate_secure_url(user_id, expiry_hours=24):
    """Generate a secure tokenized URL for medical summary"""
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    
    # In production, store this in a secure database
    url_data = {
        'token': token,
        'user_id': user_id,
        'expiry': expiry.isoformat(),
        'access_type': 'medical_summary'
    }
    
    # Save token data for validation
    with open(f'outputs/qr_token_{token}.json', 'w') as f:
        json.dump(url_data, f)
    
    return f"https://axa-safestep.com/medical/{token}"

def create_qr_code(data, filename):
    """Create QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_qr.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    # Load user profile for medical summary
    with open('profiles/health_profile_maria.json', 'r') as f:
        profile = json.load(f)
    
    # Generate secure URL
    secure_url = generate_secure_url(user_id)
    
    # Create QR code
    qr_filename = f'outputs/qr_medical_{user_id}.png'
    create_qr_code(secure_url, qr_filename)
    
    # Create medical summary data
    medical_summary = {
        'user_id': user_id,
        'name': profile['personal_info']['name'],
        'age': profile['personal_info']['age'],
        'medications': profile['medications']['current_medications'],
        'allergies': profile['medications']['allergies'],
        'emergency_contacts': profile['emergency_contacts'],
        'generated_at': datetime.now().isoformat(),
        'qr_url': secure_url,
        'qr_image': qr_filename
    }
    
    # Output result
    print(json.dumps(medical_summary, indent=2))

if __name__ == "__main__":
    main()
