#!/usr/bin/env python3
"""
Script to convert the old CSV configuration files to the new consolidated JSON format.

This is a one-time migration script. After running this, the CSV files can be removed.
"""

import csv
import json
from pathlib import Path
from datetime import datetime

def load_risk_matrix(csv_path):
    """Load the risk matrix CSV file and return a list of hazard configurations."""
    hazards = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hazard_id = row['hazard'].lower().replace(' ', '_')
            hazard = {
                'id': hazard_id,
                'display_name': row['hazard'].replace('_', ' ').title(),
                'weights': {
                    'mobility': int(row['weight_mobility']),
                    'vision': int(row['weight_vision']),
                    'cognition': int(row['weight_cognition'])
                },
                'base_score': int(row['base_score']),
                'description': f"Hazard related to {row['hazard'].replace('_', ' ').lower()}"
            }
            hazards.append(hazard)
    return hazards

def load_detection_mapping(csv_path):
    """Load the detection to hazard mapping CSV file."""
    mappings = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping = {
                'object': row['object'],
                'hazard_id': row['hazard'].lower().replace(' ', '_'),
                'example': row['example'],
                'notes': row['notes']
            }
            mappings.append(mapping)
    return mappings

def load_risk_thresholds(csv_path):
    """Load the risk thresholds CSV file."""
    thresholds = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            threshold = {
                'label': row['label'],
                'min_score': int(row['min_score']),
                'max_score': int(row['max_score']),
                'color': row['color'].lower()
            }
            thresholds.append(threshold)
    return thresholds

def main():
    # Paths to the old CSV files
    base_dir = Path(__file__).parent.parent
    risk_matrix_path = base_dir / 'axa_app_mvp' / 'logic' / 'risk_matrix_v1.csv'
    detection_mapping_path = base_dir / 'axa_app_mvp' / 'logic' / 'detection_to_hazard.csv'
    risk_thresholds_path = base_dir / 'axa_app_mvp' / 'logic' / 'risk_score_thresholds.csv'
    
    # Output path for the new JSON config
    output_path = base_dir / 'axa_app_mvp' / 'logic' / 'config.json'
    
    # Check if input files exist
    if not all([risk_matrix_path.exists(), detection_mapping_path.exists(), risk_thresholds_path.exists()]):
        print("Error: One or more input CSV files are missing.")
        print(f"Looking for:")
        print(f"- {risk_matrix_path}")
        print(f"- {detection_mapping_path}")
        print(f"- {risk_thresholds_path}")
        return 1
    
    # Load data from CSV files
    print("Loading data from CSV files...")
    hazards = load_risk_matrix(risk_matrix_path)
    detection_mappings = load_detection_mapping(detection_mapping_path)
    risk_thresholds = load_risk_thresholds(risk_thresholds_path)
    
    # Create the consolidated config
    config = {
        'version': '1.0.0',
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d'),
        'description': 'Consolidated configuration for AXA ADAPT fall hazard detection system',
        'hazards': hazards,
        'detection_mappings': detection_mappings,
        'risk_thresholds': risk_thresholds
    }
    
    # Write the config to JSON
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Successfully created {output_path}")
    print(f"You can now safely remove the old CSV files if desired:")
    print(f"- {risk_matrix_path}")
    print(f"- {detection_mapping_path}")
    print(f"- {risk_thresholds_path}")
    
    return 0

if __name__ == '__main__':
    exit(main())
