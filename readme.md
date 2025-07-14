# AXA ADAPT - Fall Hazard Detection System

<div align="center">
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#dashboard">Dashboard</a> 📄 2. Add Docstrings to Core Services and Functions
🎯 Why:
Auto-generates proper DeepWiki docs

Helps execs, junior devs, and future teammates understand logic

✅ What to Ask Augment:
text
Copy
Edit
Add type-annotated docstrings to the following:
- `QRService.generate_qr()`
- `HazardService.assess_hazards()`
- `score_hazards()` in hazard_scoring.py

Each docstring should explain purpose, parameters, return structure, and edge cases.
•
    <a href="#accessibility">Accessibility</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#api-documentation">API Docs</a> •
    <a href="#development">Development</a>
  </p>
  
  [![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-009688.svg)](https://fastapi.tiangolo.com/)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Accessibility](https://img.shields.io/badge/Accessibility-WCAG_2.1_AA-2B579A.svg)](https://www.w3.org/TR/WCAG21/)
</div>

## Features

### 🚀 New Dashboard
- Modern, intuitive interface with two main workflows
- Real-time room scan analysis with hazard detection
- Secure QR health data generator with customizable access levels
- Interactive visualizations and actionable insights

### 🔍 Room Scan Mode
- Upload room images for automatic hazard detection
- Real-time validation and progress feedback
- Risk assessment visualization with color-coded scoring
- PDF report generation with recommendations

### 🏥 QR Health Data Mode
- Multi-step form with instant validation
- Customizable access levels and privacy settings
- Expiry and security controls
- QR card personalization with photos

### ♿ Accessibility First
- WCAG 2.1 AA compliant
- Keyboard navigation and screen reader support
- High contrast and dark mode support
- Responsive design for all devices

## Tech Stack

- **Frontend**: 
  - HTML5, CSS3, JavaScript (ES6+)
  - Bootstrap 5 with AXA brand theming
  - Responsive design with mobile-first approach
  - Chart.js for data visualization

- **Backend**: 
  - FastAPI 0.95.0
  - Python 3.9+
  - Uvicorn ASGI server

- **Computer Vision**: 
  - YOLOv8 for object detection
  - OpenCV for image processing
  - Custom hazard detection algorithms

- **Data & Storage**:
  - SQLAlchemy ORM
  - SQLite (development) / PostgreSQL (production)
  - Redis for caching

- **Security**:
  - JWT Authentication
  - Rate limiting
  - CORS protection
  - Input validation

- **DevOps**:
  - Docker & Docker Compose
  - GitHub Actions for CI/CD
  - Pytest for testing
  - Pre-commit hooks

## Configuration

The application uses a consolidated JSON configuration file (`axa_app_mvp/logic/config.json`) for all hazard detection and scoring parameters. This replaces the previous CSV-based configuration system.

### Configuration Structure

```json
{
  "version": "1.0.0",
  "last_updated": "2025-07-14",
  "description": "Consolidated configuration for AXA ADAPT fall hazard detection system",
  
  "hazards": [
    {
      "id": "loose_rugs",
      "display_name": "Loose Rugs",
      "weights": {
        "mobility": 2,
        "vision": 1,
        "cognition": 1
      },
      "base_score": 10,
      "description": "Rugs that can slip or bunch up, creating a trip hazard"
    },
    ...
  ],
  
  "detection_mappings": [
    {
      "object": "rug",
      "hazard_id": "loose_rugs",
      "example": "Small throw rug in bedroom",
      "notes": "Can slip or bunch up"
    },
    ...
  ],
  
  "risk_thresholds": [
    {
      "label": "Low",
      "min_score": 0,
      "max_score": 33,
      "color": "green"
    },
    ...
  ]
}
```

### Key Sections

1. **Hazards**
   - Defines all hazard types with their properties
   - Each hazard includes:
     - `id`: Unique identifier
     - `display_name`: Human-readable name
     - `weights`: Impact weights for different user profiles
     - `base_score`: Base risk score (0-100)
     - `description`: Explanation of the hazard

2. **Detection Mappings**
   - Maps detected objects to hazard types
   - Each mapping includes:
     - `object`: Name of the detected object (from YOLO)
     - `hazard_id`: Reference to a hazard ID
     - `example`: Example scenario
     - `notes`: Additional context

3. **Risk Thresholds**
   - Defines risk categories (Low, Medium, High)
   - Each threshold includes:
     - `label`: Risk level name
     - `min_score`/`max_score`: Score range
     - `color`: Display color

### Updating Configuration

1. Edit the `config.json` file
2. No need to modify code for most changes
3. The application will automatically reload the configuration on next request

### Validation

The configuration is validated on application startup. Common validation includes:
- Required fields for each section
- Valid score ranges (0-100)
- Consistent hazard references
- Non-overlapping risk thresholds

## Prerequisites

- Python 3.9+
- Docker (optional)
- Make (for development)

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16+ (for frontend assets)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/axa/adapt-fall-prevention.git
   cd adapt-fall-prevention
   ```

2. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Set up frontend assets:
   ```bash
   cd axa_app_mvp/static
   npm install
   npm run build
   cd ../..
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python -m axa_app_mvp.db.init_db
   ```

## 🏃‍♂️ Running the Application

### Development Mode

1. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. In a new terminal, start the frontend development server:
   ```bash
   cd axa_app_mvp/static
   npm run dev
   ```

3. Access the application at: http://localhost:3000

### Production Deployment with Docker

1. Build and start the containers:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

2. The application will be available at: http://localhost:8000

3. To monitor logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

### Environment Variables

Key environment variables (set in `.env`):

```ini
# Application
APP_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///./axa_adapt.db
# For PostgreSQL: postgresql://user:password@localhost/axa_adapt

# Security
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## ♿ Accessibility Features

### Implemented
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and roles
- **High Contrast Mode**: System preference detection
- **Skip Links**: Quick access to main content
- **Form Validation**: Real-time feedback
- **Responsive Design**: Mobile-first approach

### WCAG 2.1 AA Compliance
- Perceivable: Text alternatives, time-based media, adaptable content
- Operable: Keyboard accessible, enough time, navigable
- Understandable: Readable, predictable, input assistance
- Robust: Compatible with assistive technologies

## 📊 Dashboard

The AXA ADAPT dashboard provides two main workflows:

### 1. Room Scan Mode
- Upload images of different rooms
- Automatic hazard detection
- Risk assessment based on user profile
- Detailed reports with recommendations

### 2. QR Health Data Mode
- Secure health information storage
- Customizable access levels
- Emergency medical information
- Printable QR cards

## 📚 API Documentation

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