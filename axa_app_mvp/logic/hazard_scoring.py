import csv
import os
from pathlib import Path

def load_risk_matrix(matrix_path):
    matrix = {}
    with open(matrix_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row['hazard']:
                continue
            matrix[row['hazard']] = {
                'base_score': int(row['base_score']),
                'mobility_weight': int(row['weight_mobility']),
                'vision_weight': int(row['weight_vision']),
                'cognition_weight': int(row['weight_cognition'])
            }
    return matrix

def load_thresholds(thresholds_path):
    thresholds = []
    with open(thresholds_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row['label']:
                continue
            thresholds.append({
                'label': row['label'],
                'min': int(row['min_score']),
                'max': int(row['max_score']),
                'color': row['color']
            })
    return thresholds

def load_detection_mapping(mapping_path):
    mapping = {}
    with open(mapping_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row['object'] or not row['hazard']:
                continue
            mapping[row['object']] = row['hazard']
    return mapping

def map_detected_objects_to_hazards(ai_output, mapping):
    # ai_output: list of {object, location}
    hazards = []
    for item in ai_output:
        hazard_class = mapping.get(item['object'])
        if hazard_class:
            hazards.append({
                'hazard': hazard_class,
                'object': item['object'],
                'location': item['location']
            })
    return hazards

def score_hazards(hazards, profile, matrix, thresholds):
    breakdown = []
    total_score = 0
    max_possible = 0
    for hazard in hazards:
        h = matrix.get(hazard['hazard'])
        if not h:
            continue
        base = h['base_score']
        score = base
        reason = []
        if profile.get('mobility'):
            score *= h['mobility_weight']
            reason.append('Mobility')
        if profile.get('vision'):
            score *= h['vision_weight']
            reason.append('Vision')
        if profile.get('cognition'):
            score *= h['cognition_weight']
            reason.append('Cognition')
        breakdown.append({
            'object': hazard['object'],
            'location': hazard['location'],
            'base_score': base,
            'final_score': score,
            'reason': (" and ".join(reason) + " increase risk") if reason else "Base risk"
        })
        total_score += score
        # Calculate max possible (if all weights applied)
        max_possible += base * h['mobility_weight'] * h['vision_weight'] * h['cognition_weight']
    normalized = int((total_score / max_possible) * 100) if max_possible > 0 else 0
    risk_band = next((t for t in thresholds if t['min'] <= normalized <= t['max']), None)
    return {
        'score': normalized,
        'riskLevel': risk_band['label'] if risk_band else 'Unknown',
        'color': risk_band['color'] if risk_band else 'grey',
        'hazards': breakdown,
        'recommendation': "Remove identified hazards and re-scan in 30 days"
    }
