import pytest
import os
import time
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from axa_app_mvp.logic.qr_utils import (
    generate_secure_url,
    create_qr_code
)

# Fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_token_data():
    """Sample token data for testing."""
    expiry = datetime.utcnow() + timedelta(hours=1)
    return {
        'token': 'test_token_123',
        'user_id': 'test_user_1',
        'expiry': expiry.isoformat(),
        'access_type': 'medical_summary'
    }

def test_generate_secure_url(temp_dir):
    """Test generating a secure URL with token."""
    # Test with default parameters
    url = generate_secure_url(
        user_id='test_user_1',
        output_dir=str(temp_dir)
    )
    
    assert url.startswith('https://axa-safestep.com/medical/')
    token = url.split('/')[-1]
    
    # Verify token file was created
    token_file = temp_dir / f'qr_token_{token}.json'
    assert token_file.exists()
    
    # Verify token file content
    with open(token_file) as f:
        data = json.load(f)
        assert data['user_id'] == 'test_user_1'
        assert 'token' in data
        assert 'expiry' in data
        assert data['access_type'] == 'medical_summary'

def test_generate_secure_url_custom_params(temp_dir):
    """Test generating a secure URL with custom parameters."""
    # Test with custom expiry
    url = generate_secure_url(
        user_id='test_user_2',
        expiry_hours=48,
        output_dir=str(temp_dir)
    )
    
    token = url.split('/')[-1]
    token_file = temp_dir / f'qr_token_{token}.json'
    
    # Verify token file was created with custom expiry
    with open(token_file) as f:
        data = json.load(f)
        expiry = datetime.fromisoformat(data['expiry'])
        assert (expiry - datetime.utcnow()) > timedelta(hours=47)

def test_create_qr_code(temp_dir):
    """Test QR code creation."""
    test_file = temp_dir / 'test_qr.png'
    test_data = 'https://example.com'
    
    # Test QR code creation
    create_qr_code(test_data, str(test_file))
    
    # Verify file was created and has content
    assert test_file.exists()
    assert test_file.stat().st_size > 0

def test_create_qr_code_edge_cases(temp_dir):
    """Test edge cases for QR code creation."""
    # Test with very long data
    long_data = 'a' * 1000
    test_file = temp_dir / 'long_qr.png'
    create_qr_code(long_data, str(test_file))
    assert test_file.exists()
    assert test_file.stat().st_size > 0
    
    # Test with special characters
    special_data = '!@#$%^&*()_+{}|:"<>?/.,;\'[]\-='
    test_file = temp_dir / 'special_qr.png'
    create_qr_code(special_data, str(test_file))
    assert test_file.exists()
    assert test_file.stat().st_size > 0
