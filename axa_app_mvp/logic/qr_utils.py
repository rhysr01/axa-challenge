import json
import qrcode
import uuid
from datetime import datetime, timedelta
from pathlib import Path

class TokenExpiredError(Exception):
    """Raised when a token has expired."""
    pass


class TokenValidationError(Exception):
    """Raised when a token is invalid for reasons other than expiration."""
    pass


class QRCodeError(Exception):
    """Raised when there's an error generating or processing a QR code."""
    pass

def generate_secure_url(user_id, expiry_hours=24, output_dir="outputs"):
    """
    Generate a secure tokenized URL for medical summary with fall risk assessment
    
    Args:
        user_id (str): The ID of the user
        expiry_hours (int): Number of hours until the token expires
        output_dir (str): Directory to store token files
        
    Returns:
        str: A URL containing the token
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    
    # Base URL data
    url_data = {
        'token': token,
        'user_id': user_id,
        'expiry': expiry.isoformat(),
        'access_type': 'medical_summary',
        'generated_at': datetime.now().isoformat()
    }
    
    # Try to load and include risk report if available
    risk_path = Path(output_dir) / f"risk_report_{user_id}.json"
    if risk_path.exists():
        try:
            with open(risk_path, 'r') as f:
                risk_data = json.load(f)
                # Only include non-sensitive, relevant risk data
                url_data['risk_report'] = {
                    'score': risk_data.get('total_score', 0),
                    'risk_level': risk_data.get('risk_level', 'Not assessed'),
                    'hazards': risk_data.get('hazards', []),  # Changed from hazard_details to hazards
                    'recommendation': risk_data.get('recommendation', ''),
                    'generated_at': risk_data.get('generated_at', datetime.now().isoformat())
                }
        except (json.JSONDecodeError, IOError) as e:
            # Log error but don't fail the whole operation
            print(f"Warning: Could not load risk report: {e}")
    
    # Save token data to file
    token_file = Path(output_dir) / f"qr_token_{token}.json"
    with open(token_file, 'w') as f:
        json.dump(url_data, f, indent=2)
    
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

def validate_token(token, output_dir="outputs"):
    """
    Validate a QR token and return its data if valid.
    
    Args:
        token (str): The token to validate
        output_dir (str): Directory where token files are stored
        
    Returns:
        dict: Token data if valid, None otherwise
    """
    token_file = Path(output_dir) / f"qr_token_{token}.json"
    
    # Check if token file exists
    if not token_file.exists():
        return None
        
    try:
        # Load token data
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            
        # Check if token is expired
        expiry = datetime.fromisoformat(token_data['expiry'])
        if datetime.now() > expiry:
            # Clean up expired token
            token_file.unlink(missing_ok=True)
            return None
            
        return token_data
        
    except (json.JSONDecodeError, KeyError, ValueError):
        # Clean up invalid token file
        token_file.unlink(missing_ok=True)
        return None

def cleanup_expired_tokens(output_dir="outputs"):
    """
    Clean up expired token files from the output directory.
    
    Args:
        output_dir (str): Directory where token files are stored
        
    Returns:
        tuple: (expired_count, stale_count) - Count of expired and stale tokens cleaned up
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return 0, 0
        
    expired_count = 0
    stale_count = 0
    
    # Find all token files
    for token_file in output_path.glob("qr_token_*.json"):
        try:
            # Extract token from filename
            token = token_file.stem.replace("qr_token_", "")
            
            # Check if token is expired
            token_data = validate_token(token, output_dir)
            if token_data is None:
                # If token is None, it was expired or invalid
                expired_count += 1
                
        except Exception as e:
            # If there's any error, clean up the file
            token_file.unlink(missing_ok=True)
            stale_count += 1
    
    return expired_count, stale_count
