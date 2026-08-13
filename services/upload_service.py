import os
import zipfile
import uuid
from typing import List, Dict, Any, Optional

class UploadService:
    """
    Handles file ingestion and unpacking for CarbonLedger intake.
    Returns a flat list of dict entries representing files that require OCR or structural parsing.
    """
    def __init__(self, temp_root: Optional[str] = None):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_root = temp_root or os.path.join(project_root, "output", "temp")
        os.makedirs(self.temp_root, exist_ok=True)

    def process_upload(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        ext = os.path.splitext(filename)[1].lower()
        files_to_process = []

        if ext == ".zip":
            extract_dir = os.path.join(self.temp_root, f"extracted_{uuid.uuid4().hex[:8]}")
            os.makedirs(extract_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        full_p = os.path.join(root, f)
                        if os.path.isfile(full_p):
                            files_to_process.append({"path": full_p, "name": f})
            except Exception as e:
                raise RuntimeError(f"Failed to extract ZIP archive: {e}")
        else:
            files_to_process.append({"path": file_path, "name": filename})

        return files_to_process
