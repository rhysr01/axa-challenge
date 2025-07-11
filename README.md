# AXA QR MVP

A minimal viable product for generating QR codes during AXA client onboarding processes. This project provides a FastAPI service for QR code generation and includes n8n workflow automation for seamless client onboarding.

## 🏗️ Project Structure

```
axa-qr-mvp/
├── qr/
│   ├── gen_qr.py         # Core QR generation logic
│   └── app.py            # FastAPI application
├── workflows/            # n8n workflow configurations
│   └── qr-onboard.json   # Client onboarding workflow
├── qr-codes/             # Generated QR code storage
├── requirements.txt      # Python dependencies
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- (Optional) n8n for workflow automation

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd axa-qr-mvp
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server**
   ```bash
   cd qr
   python app.py
   ```

The API will be available at `http://localhost:8000`

## 📡 API Documentation

### Core Endpoints

#### `POST /generate`
Generates a QR code for AXA client data with GDPR compliance.

**Request Body:**
```json
{
  "user_id": "user_12345",
  "axa_id_url": "https://axa.com/profile/user_12345",
  "contact": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  },
  "output_format": "png"
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_12345",
  "file_path": "qr-codes/axa_user_12345.png",
  "file_url": "/qr-codes/axa_user_12345.png",
  "message": "QR code generated successfully",
  "timestamp": "2024-01-01T12:00:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_residency": "EU",
  "consent_verified": true
}
```

**Error Responses:**
- `403 Forbidden`: User has not given consent for data processing
- `400 Bad Request`: Invalid payload format
- `500 Internal Server Error`: Processing failure

#### `GET /qr-codes/{filename}`
Serves generated QR code files.

#### `GET /health`
Health check endpoint with GDPR compliance status.

### GDPR Compliance Endpoints

#### `GET /export-data/{user_id}`
**GDPR Data Export** - Returns all data associated with a user.

**Response:**
```json
{
  "user_id": "user_12345",
  "export_timestamp": "2024-01-01T12:00:00",
  "data_residency": "EU",
  "consent_status": true,
  "qr_codes": [
    {
      "filename": "axa_user_12345.png",
      "file_path": "qr-codes/axa_user_12345.png",
      "created_at": "2024-01-01T11:30:00",
      "file_size_bytes": 2048,
      "file_format": ".png"
    }
  ],
  "activity_logs": [
    {
      "timestamp": "2024-01-01T11:30:00",
      "action": "qr_generate",
      "data_residency": "EU",
      "consent_verified": true,
      "metadata": {
        "has_axa_id_url": true,
        "has_contact_info": true,
        "output_format": "png"
      }
    }
  ],
  "export_metadata": {
    "total_qr_codes": 1,
    "total_activities": 1,
    "export_format": "json"
  }
}
```

#### `GET /consent-status/{user_id}`
Check GDPR consent status for a user.

#### `POST /admin/grant-consent/{user_id}`
Admin endpoint to grant consent for pilot users.

#### `GET /admin/consented-users`
List all users who have given consent.

### Interactive API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔄 n8n Workflow

The project includes a pre-configured n8n workflow for automated client onboarding:

### Workflow Steps:
1. **Webhook Trigger** - Receives new AXA client data
2. **QR Generation** - Calls `/generate` endpoint
3. **GitHub Commit** - Saves QR code to repository
4. **Slack Notification** - Sends success notification

### Setup n8n Workflow:

1. **Import workflow**
   ```bash
   # Import workflows/qr-onboard.json into your n8n instance
   ```

2. **Configure credentials**
   - GitHub credentials for repository access
   - Slack credentials for notifications

3. **Set webhook URL**
   - Use the webhook URL provided by n8n
   - Configure your systems to POST to this URL

### Webhook Payload Example:
```json
{
  "user_id": "client_001",
  "axa_id_url": "https://axa.com/profile/client_001",
  "contact": {
    "name": "Jane Smith",
    "email": "jane.smith@company.com",
    "phone": "+1987654321"
  },
  "github_owner": "your-org",
  "github_repo": "axa-qr-mvp"
}
```

## 🔧 Development

### Running Tests
```bash
# Add your test commands here
pytest tests/
```

### Code Quality
```bash
# Format code
black qr/
isort qr/

# Lint code  
flake8 qr/
mypy qr/
```

### Environment Variables
```bash
# Optional configuration
export QR_OUTPUT_DIR=qr-codes
export API_HOST=0.0.0.0
export API_PORT=8000
```

## 📁 QR Code Storage

Generated QR codes are stored in the `qr-codes/` directory with the naming convention:
- Format: `axa_{user_id}.{format}`
- Example: `axa_user_12345.png`

## 🔒 Security & GDPR Compliance

### GDPR Features (Lite Implementation)
- ✅ **Consent Management**: Users must have consent before QR generation
- ✅ **Regulatory Logging**: All actions logged for audit trail  
- ✅ **Data Export**: Users can export all their data (`/export-data/{user_id}`)
- ✅ **Data Residency**: Hard-coded EU region for compliance
- ✅ **Audit Trail**: Structured JSON logs with request IDs and payload hashes

### Regulatory Logging
All QR generation requests are logged to `regulatory_audit.log` with:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "actor": "user_12345", 
  "action": "qr_generate",
  "payload_hash": "sha256:abc123...",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data_residency": "EU",
  "consent_verified": true,
  "metadata": {"has_axa_id_url": true, "output_format": "png"}
}
```

### Consent Management
- Pre-populated consent store for pilot users
- Admin endpoints for consent management
- 403 errors for users without consent

### Additional Security Considerations
- Validate all input data before QR generation
- Implement rate limiting for the API  
- Secure webhook endpoints with proper authentication
- Consider encrypting sensitive data in QR codes
- Monitor regulatory audit logs regularly

## 🛠️ Customization

### QR Code Settings
Modify `qr/gen_qr.py` to customize:
- QR code size and error correction
- Image formats (PNG, SVG)
- Data encoding schemes

### API Configuration
Update `qr/app.py` to:
- Add authentication middleware
- Implement custom validation
- Add monitoring and logging

## 📦 Deployment

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY qr/ ./qr/
COPY qr-codes/ ./qr-codes/

EXPOSE 8000
CMD ["python", "qr/app.py"]
```

### Production Considerations
- Use environment variables for configuration
- Implement proper logging and monitoring
- Set up backup for generated QR codes
- Configure reverse proxy (nginx/Apache)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
- Create an issue in this repository
- Contact the development team
- Check the API documentation at `/docs`

---

**Happy coding! 🎉**