import json
import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Data residency configuration
DATA_RESIDENCY_REGION = os.getenv("DATA_RESIDENCY_REGION", "EU")

# Simple consent store (in production, this would be a database)
CONSENT_STORE: Dict[str, bool] = {
    # Pilot users with consent
    "user_12345": True,
    "pilot_user_001": True,
    "test_user_axa": True,
    "demo_client_123": True,
}

@dataclass
class RegulatoryLogEntry:
    """Structured regulatory log entry for audit compliance."""
    timestamp: str
    actor: str
    action: str
    payload_hash: str
    request_id: str
    data_residency: str
    consent_verified: bool
    metadata: Optional[Dict[str, Any]] = None

class RegulatoryLogger:
    """Handles GDPR-compliant audit logging."""
    
    def __init__(self, log_file_path: str = "regulatory_audit.log"):
        self.log_file_path = log_file_path
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup dedicated regulatory logger."""
        logger = logging.getLogger("regulatory_audit")
        logger.setLevel(logging.INFO)
        
        # Ensure we don't duplicate handlers
        if not logger.handlers:
            handler = logging.FileHandler(self.log_file_path)
            formatter = logging.Formatter('%(message)s')  # Raw JSON output
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def log_qr_generation(
        self, 
        user_id: str, 
        payload: Dict[str, Any], 
        request_id: str,
        consent_verified: bool
    ) -> None:
        """Log QR code generation for regulatory compliance."""
        
        # Create payload hash for privacy
        payload_json = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        
        entry = RegulatoryLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=user_id,
            action="qr_generate",
            payload_hash=payload_hash,
            request_id=request_id,
            data_residency=DATA_RESIDENCY_REGION,
            consent_verified=consent_verified,
            metadata={
                "has_axa_id_url": "axa_id_url" in payload,
                "has_contact_info": "contact" in payload,
                "output_format": payload.get("output_format", "png")
            }
        )
        
        # Log as structured JSON
        self.logger.info(json.dumps(asdict(entry)))
    
    def log_data_export(self, user_id: str, request_id: str) -> None:
        """Log data export request for audit trail."""
        
        entry = RegulatoryLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=user_id,
            action="data_export",
            payload_hash="n/a",
            request_id=request_id,
            data_residency=DATA_RESIDENCY_REGION,
            consent_verified=True,  # Export is a user right, doesn't need consent
            metadata={"export_type": "full_user_data"}
        )
        
        self.logger.info(json.dumps(asdict(entry)))

class ConsentManager:
    """Manages user consent for GDPR compliance."""
    
    @staticmethod
    def has_consent(user_id: str) -> bool:
        """Check if user has given consent for data processing."""
        return CONSENT_STORE.get(user_id, False)
    
    @staticmethod
    def grant_consent(user_id: str) -> None:
        """Grant consent for user (for manual pilot user setup)."""
        CONSENT_STORE[user_id] = True
    
    @staticmethod
    def revoke_consent(user_id: str) -> None:
        """Revoke consent for user."""
        CONSENT_STORE[user_id] = False
    
    @staticmethod
    def list_consented_users() -> List[str]:
        """List all users who have given consent."""
        return [user_id for user_id, consent in CONSENT_STORE.items() if consent]

class DataExporter:
    """Handles GDPR data export requests."""
    
    def __init__(self, regulatory_logger: RegulatoryLogger):
        self.regulatory_logger = regulatory_logger
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all data associated with a user."""
        
        # Get QR code files
        qr_codes = self._get_user_qr_codes(user_id)
        
        # Get audit logs
        activity_logs = self._get_user_activity_logs(user_id)
        
        # Get consent status
        consent_status = ConsentManager.has_consent(user_id)
        
        return {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "data_residency": DATA_RESIDENCY_REGION,
            "consent_status": consent_status,
            "qr_codes": qr_codes,
            "activity_logs": activity_logs,
            "export_metadata": {
                "total_qr_codes": len(qr_codes),
                "total_activities": len(activity_logs),
                "export_format": "json"
            }
        }
    
    def _get_user_qr_codes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all QR codes generated for this user."""
        qr_codes = []
        qr_codes_dir = Path("qr-codes")
        
        if qr_codes_dir.exists():
            # Look for files matching user pattern
            pattern = f"axa_{user_id}.*"
            for file_path in qr_codes_dir.glob(pattern):
                stat = file_path.stat()
                qr_codes.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "file_size_bytes": stat.st_size,
                    "file_format": file_path.suffix.lower()
                })
        
        return qr_codes
    
    def _get_user_activity_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Extract user's activity from regulatory logs."""
        activity_logs = []
        
        if not os.path.exists(self.regulatory_logger.log_file_path):
            return activity_logs
        
        try:
            with open(self.regulatory_logger.log_file_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('actor') == user_id:
                            activity_logs.append({
                                "timestamp": log_entry.get('timestamp'),
                                "action": log_entry.get('action'),
                                "data_residency": log_entry.get('data_residency'),
                                "consent_verified": log_entry.get('consent_verified'),
                                "metadata": log_entry.get('metadata', {})
                            })
                    except json.JSONDecodeError:
                        continue  # Skip malformed log lines
        except FileNotFoundError:
            pass  # No logs yet
        
        return sorted(activity_logs, key=lambda x: x['timestamp'], reverse=True)

# Global instances
regulatory_logger = RegulatoryLogger()
data_exporter = DataExporter(regulatory_logger)