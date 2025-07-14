# AXA ADAPT - Fall Hazard Detection System

<div align="center">
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#api-documentation">API Docs</a> •
    <a href="#development">Development</a>
  </p>
  
  [![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0-009688.svg)](https://fastapi.tiangolo.com/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

## Features

- Image-based hazard detection using YOLOv8
- Risk scoring based on user profiles (mobility, vision, cognition)
- Secure QR code generation for health data access
- Responsive web interface for results visualization
- Scalable API architecture

## Tech Stack

- **Backend**: FastAPI
- **Computer Vision**: YOLOv8, OpenCV
- **Authentication**: JWT Tokens
- **Data Processing**: NumPy, Pillow
- **QR Generation**: qrcode
- **Testing**: Pytest
- **Containerization**: Docker

## Prerequisites

- Python 3.9+
- Docker (optional)
- Make (for development)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/axa-adapt.git
   cd axa-adapt
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Application

### Development

```bash
uvicorn main:app --reload
```

### Production (Docker)

```bash
docker build -t axa-adapt .
docker run -p 8000:8000 axa-adapt
```

## API Documentation

### Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### 1. Hazard Assessment

**Endpoint**: `POST /assess-hazards`

Submit room images for hazard analysis.

**Request Format**:
```http
POST /assess-hazards
Content-Type: multipart/form-data

{
  "sitting_room": [binary image data],
  "bathroom": [binary image data],
  "hallway": [binary image data],
  "steps": [binary image data],
  "bedroom": [binary image data],
  "profile_json": "{\"mobility\": true, \"vision\": false, \"cognition\": true, \"age\": 75}"
}
```

**Response Example (200 OK)**:
```json
{
  "score": 65,
  "riskLevel": "Medium",
  "hazards": [
    {
      "object": "rug",
      "hazard": "loose_rugs",
      "location": {"x": 100, "y": 200},
      "base_score": 10,
      "final_score": 20,
      "riskLevel": "High"
    }
  ],
  "recommendation": "Consider removing loose rugs and improving lighting..."
}
```

#### 2. Generate QR Code

**Endpoint**: `POST /generate-qr`

Generate a secure QR code for health data access.

**Request Format**:
```http
POST /generate-qr
Content-Type: application/json

{
  "user_id": "user123",
  "access_type": "medical_summary",
  "expiry_hours": 24,
  "metadata": {"consent": ["emergency_contacts", "medications"]}
}
```

**Response Example (200 OK)**:
```json
{
  "qr_url": "http://localhost:8000/qr/user123?token=abc123",
  "expires_at": "2025-07-14T22:50:01Z",
  "access_type": "medical_summary"
}
```

#### 3. View Health Summary

**Endpoint**: `GET /qr/{user_id}`

View health summary via QR code.

**Request Format**:
```http
GET /qr/user123?token=abc123
```

**Response**: HTML page with health summary

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v

# With coverage report
pytest --cov=axa_app_mvp tests/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | `your-secret-key` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | JWT token expiration | `24` |
| `QR_TOKEN_EXPIRE_HOURS` | QR code expiration | `24` |
| `OUTPUT_DIR` | Directory for generated files | `./outputs` |
| `PROFILES_DIR` | Directory for user profiles | `./axa_app_mvp/profiles` |

## Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t axa-adapt .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e SECRET_KEY=your-secret-key \
     -e ACCESS_TOKEN_EXPIRE_HOURS=24 \
     axa-adapt
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact support@example.com or open an issue in the repository.

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables Not Set**:
   Ensure all required environment variables are set in `.env`

3. **Port Already in Use**:
   ```bash
   lsof -i :8000  # Find process using port 8000
   kill -9 <PID>  # Replace <PID> with the process ID
   ```

4. **Docker Build Fails**:
   - Check Docker is running
   - Ensure Docker has enough resources (CPU/Memory)
   - Try rebuilding with `--no-cache` flag

## Monitoring

Application metrics are available at `/metrics` (Prometheus format).

## Security

- All sensitive routes require authentication
- QR tokens are single-use and expire
- Input validation on all endpoints
- Rate limiting on authentication endpoints

## Print Button

<div style="text-align: right; margin-bottom: 20px;">
  <button onclick="window.print()" style="background-color: #0056b3; color: white; border: none; padding: 12px 24px; font-size: 18px; border-radius: 5px; cursor: pointer;">
    🖨️ Print This Guide
  </button>
</div>

## Screenshots

<div style="text-align: center; margin: 30px 0;">
  <h3 style="color: #0056b3; font-size: 24px;">See How It Works</h3>
  
  <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin: 20px 0;">
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Screenshot: Home Screen]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">1. Home Screen</h4>
        <p style="margin: 0; font-size: 16px;">Start by tapping the camera button to begin scanning your home.</p>
      </div>
    </div>
    
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Screenshot: Camera View]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">2. Take Photos</h4>
        <p style="margin: 0; font-size: 16px;">Take clear photos of each room, focusing on floors and walkways.</p>
      </div>
    </div>
    
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Screenshot: Results]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">3. View Results</h4>
        <p style="margin: 0; font-size: 16px;">Get your safety score and improvement suggestions.</p>
      </div>
    </div>
  </div>
</div>

## Visual Examples

<div style="text-align: center; margin: 30px 0;">
  <h3 style="color: #0056b3; font-size: 24px;">Example Use Cases</h3>
  
  <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin: 20px 0;">
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Example: Hazard Detection]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">Hazard Detection</h4>
        <p style="margin: 0; font-size: 16px;">Detect potential fall hazards in your home.</p>
      </div>
    </div>
    
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Example: QR Code Generation]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">QR Code Generation</h4>
        <p style="margin: 0; font-size: 16px;">Generate a secure QR code for health data access.</p>
      </div>
    </div>
    
    <div style="width: 300px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
      <div style="height: 200px; background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #666; font-size: 18px;">
        [Example: Health Summary]
      </div>
      <div style="padding: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #0056b3;">Health Summary</h4>
        <p style="margin: 0; font-size: 16px;">View your health summary and track your progress.</p>
      </div>
    </div>
  </div>
</div>

<!-- Print Styles -->
<style>
  @media print {
    button { display: none !important; }
    #printable-content { max-width: 100%; padding: 0; }
    .no-print { display: none !important; }
    a { color: #0056b3 !important; text-decoration: underline !important; }
  }
</style>