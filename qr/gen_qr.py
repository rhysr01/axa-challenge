import qrcode
import qrcode.constants
import json
import os
from typing import Dict, Any, Optional
from PIL import Image


def generate_qr_code(
    user_data: Dict[str, Any], 
    user_id: str,
    output_format: str = "png",
    output_dir: str = "qr-codes"
) -> str:
    """
    Generate QR code for AXA user data.
    
    Args:
        user_data: Dictionary containing user information (AXA-ID URL, contact JSON, etc.)
        user_id: Unique identifier for the user
        output_format: Output format ('png' or 'svg')
        output_dir: Directory to save the QR code
        
    Returns:
        str: Path to the generated QR code file
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert user data to JSON string for QR encoding
    qr_data = json.dumps(user_data, indent=2)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR Code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Generate filename
    filename = f"axa_{user_id}.{output_format}"
    filepath = os.path.join(output_dir, filename)
    
    if output_format.lower() == "svg":
        # Generate SVG
        from qrcode.image.svg import SvgPathImage
        img = qr.make_image(image_factory=SvgPathImage)
        with open(filepath, 'wb') as f:
            img.save(f)
    else:
        # Generate PNG (default)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filepath)
    
    return filepath


def generate_axa_qr(axa_id_url: str, user_id: str, contact_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function to generate QR for AXA ID URL with optional contact info.
    
    Args:
        axa_id_url: The AXA ID URL
        user_id: User identifier
        contact_info: Optional contact information dictionary
        
    Returns:
        str: Path to generated QR code
    """
    
    user_data: Dict[str, Any] = {
        "axa_id_url": axa_id_url,
        "user_id": user_id,
        "type": "axa_onboarding"
    }
    
    if contact_info:
        user_data["contact"] = contact_info
    
    return generate_qr_code(user_data, user_id)


def validate_user_payload(payload: Dict[str, Any]) -> bool:
    """
    Validate that the user payload contains required fields.
    
    Args:
        payload: User data payload
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["user_id"]
    
    for field in required_fields:
        if field not in payload:
            return False
    
    # At least one of these should be present
    if "axa_id_url" not in payload and "contact" not in payload:
        return False
    
    return True