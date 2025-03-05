"""
Database configuration for ChromaDB used by the Research Crew.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def configure_chromadb():
    """Configure the ChromaDB environment."""
    try:
        # Create a persistent directory for ChromaDB
        db_dir = Path("./chroma_db")
        db_dir.mkdir(exist_ok=True)
        
        # Set environment variables for ChromaDB - using the new client format
        os.environ["CHROMA_PERSIST_DIRECTORY"] = str(db_dir.absolute())
        
        # Set additional ChromaDB settings for new client format
        os.environ["CHROMA_CLIENT_SETTINGS"] = '{"anonymized_telemetry": false}'
        
        logger.info(f"ChromaDB configured to use directory: {db_dir.absolute()}")
        return True
    except Exception as e:
        logger.error(f"Error configuring ChromaDB: {str(e)}")
        return False 