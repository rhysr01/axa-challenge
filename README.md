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

### Endpoints

#### `POST /generate`
Generates a QR code for AXA client data.

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
  "timestamp": "2024-01-01T12:00:00"
}
```

#### `GET /qr-codes/{filename}`
Serves generated QR code files.

#### `GET /health`
Health check endpoint for monitoring.

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

## 🔒 Security Considerations

- Validate all input data before QR generation
- Implement rate limiting for the API
- Secure webhook endpoints with proper authentication
- Consider encrypting sensitive data in QR codes

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