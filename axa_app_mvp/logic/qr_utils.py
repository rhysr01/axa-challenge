import json
import qrcode
import uuid
from datetime import datetime, timedelta
from pathlib import Path

def generate_secure_url(user_id, expiry_hours=24, output_dir="outputs"):
    """Generate a secure tokenized URL for medical summary"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    url_data = {
        'token': token,
        'user_id': user_id,
        'expiry': expiry.isoformat(),
        'access_type': 'medical_summary'
    }
    with open(f'{output_dir}/qr_token_{token}.json', 'w') as f:
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
