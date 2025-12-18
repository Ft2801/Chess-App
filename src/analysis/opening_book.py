import json
import os
from typing import Optional, Dict

def get_opening_name(fen: str) -> Optional[str]:
    """
    Get the opening name for a given FEN string from the openings database.
    Matches logic from wintrchess/shared/src/lib/reporter/utils/opening.ts
    """
    # Load openings database
    # Assuming openings.json is in src/resources/openings.json relative to project root
    # or relative to this file? Let's try relative to this file for robustness if possible,
    # or absolute path based on project structure.
    
    # Construct path to resources/openings.json from src/analysis/opening_book.py
    # src/analysis/../resources/openings.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resource_path = os.path.join(base_dir, "resources", "openings.json")
    
    try:
        with open(resource_path, 'r', encoding='utf-8') as f:
            openings_db: Dict[str, str] = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

    # Extract piece placement part of FEN (first field)
    fen_pieces = fen.split(" ")[0]
    
    if not fen_pieces:
        return None
        
    return openings_db.get(fen_pieces)
