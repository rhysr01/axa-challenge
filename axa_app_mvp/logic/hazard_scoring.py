import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class HazardConfig:
    def __init__(self, config_path: str):
        """
        Load and manage the consolidated configuration.
        
        Args:
            config_path: Path to the config.json file
        """
        self.config = self._load_config(config_path)
        self.hazards = self._process_hazards()
        self.detection_mapping = self._process_detection_mapping()
        self.risk_thresholds = self.config['risk_thresholds']
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate the JSON configuration."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Basic validation
        required_sections = ['hazards', 'detection_mappings', 'risk_thresholds']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section in config: {section}")
                
        return config
    
    def _process_hazards(self) -> Dict[str, Dict]:
        """Process hazards into a dictionary for easy lookup."""
        return {hazard['id']: hazard for hazard in self.config['hazards']}
    
    def _process_detection_mapping(self) -> Dict[str, str]:
        """Process detection mappings into a simple object -> hazard_id mapping."""
        return {mapping['object']: mapping['hazard_id'] 
                for mapping in self.config['detection_mappings']}
    
    def get_hazard(self, hazard_id: str) -> Optional[Dict]:
        """Get hazard configuration by ID."""
        return self.hazards.get(hazard_id)
    
    def get_hazard_for_object(self, object_name: str) -> Optional[Dict]:
        """Get hazard configuration for a detected object."""
        hazard_id = self.detection_mapping.get(object_name)
        return self.get_hazard(hazard_id) if hazard_id else None
    
    def get_risk_level(self, score: float) -> Dict:
        """Determine risk level based on score."""
        for threshold in self.risk_thresholds:
            if threshold['min_score'] <= score <= threshold['max_score']:
                return threshold
        return self.risk_thresholds[-1]  # Default to highest risk if no match

def map_detected_objects_to_hazards(ai_output, config):
    """
    Map detected objects to their corresponding hazards using the configuration.
    
    Args:
        ai_output: List of dictionaries with 'object' and optional 'location' keys
        config: Instance of HazardConfig
        
    Returns:
        List of dictionaries with hazard information
    """
    hazards = []
    for item in ai_output:
        hazard = config.get_hazard_for_object(item['object'])
        if hazard:
            hazards.append({
                'hazard_id': hazard['id'],
                'hazard_name': hazard['display_name'],
                'location': item.get('location', 'unknown'),
                'object': item['object'],
                'base_score': hazard['base_score'],
                'weights': hazard['weights']
            })
    return hazards

def score_hazards(hazards, profile, config, thresholds):
    """
    Calculate risk scores for detected hazards based on user profile.
    
    Args:
        hazards: List of detected hazards with their configurations
        profile: User profile with mobility, vision, cognition scores (0-1)
        config: Instance of HazardConfig
        thresholds: Risk threshold configurations
        
    Returns:
        Dictionary containing:
        - total_score: Overall risk score (0-100)
        - risk_level: Text description of risk level
        - color: Color code for display
        - hazard_details: List of individual hazard scores and details
    """
    if not hazards:
        return {
            'total_score': 0,
            'risk_level': 'None',
            'color': 'green',
            'hazard_details': [],
            'recommendation': 'No hazards detected. Consider scheduling a follow-up scan in 6 months.'
        }
    
    hazard_scores = []
    total_score = 0
    
    # Calculate score for each hazard
    for hazard in hazards:
        hazard_config = config.get_hazard(hazard['hazard_id'])
        if not hazard_config:
            continue
            
        # Get weights from hazard config
        weights = hazard_config.get('weights', {})
        base_score = hazard_config.get('base_score', 0)
        
        # Calculate weighted score (0-100)
        mobility_impact = profile.get('mobility', 0) * weights.get('mobility', 1)
        vision_impact = profile.get('vision', 0) * weights.get('vision', 1)
        cognition_impact = profile.get('cognition', 0) * weights.get('cognition', 1)
        
        # Calculate hazard score (0-100)
        hazard_score = base_score * (1 + (mobility_impact + vision_impact + cognition_impact) / 3)
        hazard_score = min(max(0, hazard_score), 100)  # Clamp to 0-100
        
        hazard_scores.append({
            'hazard_id': hazard['hazard_id'],
            'hazard_name': hazard['hazard_name'],
            'object': hazard.get('object', 'unknown'),
            'location': hazard.get('location', 'unknown'),
            'score': round(hazard_score, 1),
            'base_score': base_score,
            'weights': weights
        })
        
        total_score += hazard_score
    
    # Calculate average score if we have hazards
    if hazard_scores:
        total_score = total_score / len(hazard_scores)
    
    # Determine risk level
    risk_level = config.get_risk_level(total_score)
    
    return {
        'total_score': round(total_score, 1),
        'risk_level': risk_level['label'],
        'color': risk_level['color'],
        'hazard_details': hazard_scores,
        'recommendation': "Remove identified hazards and re-scan in 30 days"
    }
