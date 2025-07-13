"""
File storage utility that handles both local and cloud storage.
"""
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional, Union
import logging

logger = logging.getLogger(__name__)

class Storage:
    """Handles file storage operations with support for local and cloud storage."""
    
    def __init__(self, base_path: str = None):
        """Initialize storage with base path.
        
        Args:
            base_path: Base directory for local storage
        """
        self.base_path = Path(base_path or 'outputs')
        self.base_path.mkdir(exist_ok=True, parents=True)
    
    def save_file(self, file_data: Union[bytes, BinaryIO], file_path: str) -> str:
        """Save file to storage.
        
        Args:
            file_data: File data as bytes or file-like object
            file_path: Relative path where file should be saved
            
        Returns:
            str: Path where file was saved
        """
        dest_path = self.base_path / file_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if isinstance(file_data, bytes):
                with open(dest_path, 'wb') as f:
                    f.write(file_data)
            else:
                with open(dest_path, 'wb') as f:
                    shutil.copyfileobj(file_data, f)
            
            logger.info(f"File saved to {dest_path}")
            return str(dest_path)
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {str(e)}")
            raise
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file contents.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            File contents as bytes, or None if not found
        """
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return (self.base_path / file_path).exists()
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            bool: True if file was deleted, False if it didn't exist
        """
        full_path = self.base_path / file_path
        try:
            if full_path.exists():
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False


# Initialize storage with path from environment or default
storage = Storage(os.getenv('STORAGE_PATH', 'outputs'))
