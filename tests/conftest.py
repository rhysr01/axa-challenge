"""Configuration and fixtures for tests."""
import os
import tempfile
import pytest
from pathlib import Path
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data directories
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_output"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Create test output directory if it doesn't exist
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)

    # Set environment variables for testing
    os.environ["ENV"] = "test"

    yield  # This is where the testing happens

    # Cleanup after tests if needed
    # Remove any test files created during testing
    for item in TEST_OUTPUT_DIR.glob("*"):
        if item.is_file():
            item.unlink()

    # Remove the test output directory if empty
    try:
        TEST_OUTPUT_DIR.rmdir()
    except OSError:
        pass


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is automatically removed after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_hazard_data():
    """Sample hazard data for testing."""
    return [
        {
            'object': 'rug',
            'location': {'x': 100, 'y': 200, 'width': 50, 'height': 50},
            'confidence': 0.95
        },
        {
            'object': 'light_bulb_out',
            'location': {'x': 300, 'y': 150, 'width': 20, 'height': 20},
            'confidence': 0.85
        }
    ]


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return {
        'mobility': True,
        'vision': False,
        'cognition': False,
        'age': 75
    }


@pytest.fixture
def sample_risk_matrix():
    """Sample risk matrix for testing."""
    return {
        'loose_rugs': {
            'base_score': 10,
            'mobility_weight': 2,
            'vision_weight': 1,
            'cognition_weight': 1
        },
        'poor_lighting': {
            'base_score': 8,
            'mobility_weight': 1,
            'vision_weight': 2,
            'cognition_weight': 1
        },
        'steps_or_thresholds': {
            'base_score': 12,
            'mobility_weight': 2,
            'vision_weight': 1,
            'cognition_weight': 2
        }
    }


@pytest.fixture
def sample_thresholds():
    """Sample risk thresholds for testing."""
    return [
        {'label': 'Low', 'min': 0, 'max': 33, 'color': 'green'},
        {'label': 'Medium', 'min': 34, 'max': 66, 'color': 'yellow'},
        {'label': 'High', 'min': 67, 'max': 100, 'color': 'red'}
    ]


@pytest.fixture
def sample_detection_mapping():
    """Sample detection to hazard mapping for testing."""
    return {
        'rug': 'loose_rugs',
        'light_bulb_out': 'poor_lighting',
        'threshold': 'steps_or_thresholds'
    }
