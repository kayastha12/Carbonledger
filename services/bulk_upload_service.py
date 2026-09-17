import os
import time
import json
import uuid
import threading
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from api.database import get_db_connection
from services.universal_upload_service import UniversalUploadService

class BulkUploadService:
    """
    Manages asynchronous bulk invoice intake, batch job scheduling, live timer tracking,
    and partial calculation persistence.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.universal_service = UniversalUploadService()
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.batch_storage_dir = os.path.join(self.project_root, "output", "uploads", "batches")
        os.makedirs(self.batch_storage_dir, exist_ok=True)

    def start_bulk_upload(self, files: List[Tuple[str, bytes]], user_id: int = 1) -> Dict[str, Any]:
        """Convenience method for bulk processing invocation."""
        return self.start_batch(user_id=user_id, files=files)

    def start_batch(self, user_id: int, files: List[Tuple[str, bytes]]) -> Dict[str, Any]:
        """
        Initializes a batch and kicks off background processing for all uploaded files.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        batch_dir = os.path.join(self.batch_storage_dir, batch_id)
        os.makedirs(batch_dir, exist_ok=True)

        now_str = datetime.now().isoformat()
        total_files = len(files)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert batch header
        cursor.execute("""
        INSERT INTO upload_batches 
        (batch_id, user_id, status, total_files, processed_count, completed_count, review_count, failed_count, current_file, started_at, created_at)
        VALUES (?, ?, 'PROCESSING', ?, 0, 0, 0, 0, ?, ?, ?)
        """, (batch_id, user_id, total_files, files[0][0] if files else None, now_str, now_str))

        saved_jobs = []
        for filename, file_bytes in files:
            job_id = f"job_{uuid.uuid4().hex[:8]}"
            safe_filename = os.path.basename(filename)
            file_dest = os.path.join(batch_dir, f"{job_id}_{safe_filename}")
            
            with open(file_dest, "wb") as f:
                f.write(file_bytes)

            cursor.execute("""
            INSERT INTO batch_jobs
            (job_id, batch_id, user_id, filename, upload_id, status, extracted_count, calculated_count, review_count, total_co2e_kg, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'QUEUED', 0, 0, 0, 0.0, NULL, ?, ?)
            """, (job_id, batch_id, user_id, safe_filename, None, now_str, now_str))

            saved_jobs.append({
                "job_id": job_id,
                "filename": safe_filename,
                "file_path": file_dest
            })

        conn.commit()
        conn.close()

        # Launch background processing worker thread
        worker = threading.Thread(
            target=self._process_batch_async,
            args=(batch_id, user_id, saved_jobs),
            daemon=True
        )
        worker.start()

        return {
            "batch_id": batch_id,
            "status": "PROCESSING",
            "total_files": total_files,
            "started_at": now_str,
            "message": f"Bulk processing started for {total_files} invoices."
        }

    def _process_batch_async(self, batch_id: str, user_id: int, jobs: List[Dict[str, Any]]):
        """
        Background worker processing each invoice sequentially through the extraction,
        normalization, factor matching, and calculation pipeline.
        """
        for idx, job in enumerate(jobs, start=1):
            job_id = job["job_id"]
            filename = job["filename"]
            file_path = job["file_path"]
            now_iso = datetime.now().isoformat()

            # Update current active file
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE upload_batches SET current_file = ? WHERE batch_id = ?", (filename, batch_id))
            cursor.execute("UPDATE batch_jobs SET status = 'EXTRACTING', updated_at = ? WHERE job_id = ?", (now_iso, job_id))
            conn.commit()
            conn.close()

            try:
                # 1. Process document extraction
                upload_res = self.universal_service.process_universal_file(file_path, filename=filename)
                records = upload_res.get("records", [])
                extracted_count = len(records)
                upload_id = f"up_batch_{job_id[:8]}"

                if extracted_count == 0:
                    # No readable carbon line items
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE batch_jobs 
                    SET status = 'FAILED', error_message = 'No readable transactional activity records found', updated_at = ?
                    WHERE job_id = ?
                    """, (datetime.now().isoformat(), job_id))
                    cursor.execute("""
                    UPDATE upload_batches 
                    SET processed_count = processed_count + 1, failed_count = failed_count + 1 
                    WHERE batch_id = ?
                    """, (batch_id,))
                    conn.commit()
                    conn.close()
                    continue

                # 2. Execute carbon calculations and persistence
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE batch_jobs SET status = 'CALCULATING', upload_id = ?, extracted_count = ?, updated_at = ? WHERE job_id = ?", (upload_id, extracted_count, datetime.now().isoformat(), job_id))
                conn.commit()
                conn.close()

                calc_res = self.universal_service.calculate_and_save(records, upload_id=upload_id)
                summary = calc_res.get("summary", {})
                
                calculated_count = summary.get("rows_calculated", 0)
                review_count = summary.get("rows_manual_review", 0)
                total_co2e = summary.get("total_co2e_kg", 0.0)

                # Link upload sessions and calculation results to the user
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE upload_sessions SET user_id = ? WHERE upload_id = ?", (user_id, upload_id))
                cursor.execute("UPDATE calculation_results SET user_id = ? WHERE upload_id = ?", (user_id, upload_id))
                cursor.execute("UPDATE extracted_records SET user_id = ? WHERE upload_id = ?", (user_id, upload_id))

                job_status = "COMPLETED" if review_count == 0 else "REVIEW_REQUIRED"
                cursor.execute("""
                UPDATE batch_jobs 
                SET status = ?, extracted_count = ?, calculated_count = ?, review_count = ?, total_co2e_kg = ?, updated_at = ?
                WHERE job_id = ?
                """, (job_status, extracted_count, calculated_count, review_count, total_co2e, datetime.now().isoformat(), job_id))

                if job_status == "COMPLETED":
                    cursor.execute("UPDATE upload_batches SET processed_count = processed_count + 1, completed_count = completed_count + 1 WHERE batch_id = ?", (batch_id,))
                else:
                    cursor.execute("UPDATE upload_batches SET processed_count = processed_count + 1, review_count = review_count + 1 WHERE batch_id = ?", (batch_id,))

                conn.commit()
                conn.close()

            except Exception as e:
                # Catch per-file errors without breaking the batch
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE batch_jobs 
                SET status = 'FAILED', error_message = ?, updated_at = ?
                WHERE job_id = ?
                """, (str(e), datetime.now().isoformat(), job_id))
                cursor.execute("""
                UPDATE upload_batches 
                SET processed_count = processed_count + 1, failed_count = failed_count + 1 
                WHERE batch_id = ?
                """, (batch_id,))
                conn.commit()
                conn.close()

        # Finalize batch state
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT total_files, processed_count, completed_count, review_count, failed_count FROM upload_batches WHERE batch_id = ?", (batch_id,))
        b_row = cursor.fetchone()

        if b_row:
            completed_c = b_row["completed_count"]
            review_c = b_row["review_count"]
            failed_c = b_row["failed_count"]
            total_f = b_row["total_files"]

            if completed_c == total_f:
                final_status = "COMPLETED"
            elif completed_c + review_c > 0:
                final_status = "COMPLETED_WITH_REVIEW"
            else:
                final_status = "FAILED"

            cursor.execute("""
            UPDATE upload_batches 
            SET status = ?, current_file = NULL, completed_at = ?
            WHERE batch_id = ?
            """, (final_status, datetime.now().isoformat(), batch_id))
            conn.commit()

        conn.close()

    def get_batch_status(self, batch_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Queries database for live batch status, real-time timer calculations, and per-job items.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM upload_batches WHERE batch_id = ? AND user_id = ?", (batch_id, user_id))
        b_row = cursor.fetchone()

        if not b_row:
            conn.close()
            return None

        cursor.execute("SELECT * FROM batch_jobs WHERE batch_id = ? ORDER BY ROWID ASC", (batch_id,))
        job_rows = cursor.fetchall()
        conn.close()

        total_files = b_row["total_files"]
        processed_count = b_row["processed_count"]
        completed_count = b_row["completed_count"]
        review_count = b_row["review_count"]
        failed_count = b_row["failed_count"]
        current_file = b_row["current_file"]
        status = b_row["status"]

        started_at_str = b_row["started_at"]
        completed_at_str = b_row["completed_at"]

        # Calculate exact elapsed seconds from started_at
        elapsed_seconds = 0
        if started_at_str:
            try:
                start_dt = datetime.fromisoformat(started_at_str)
                end_dt = datetime.fromisoformat(completed_at_str) if completed_at_str else datetime.now()
                elapsed_seconds = max(0, int((end_dt - start_dt).total_seconds()))
            except Exception:
                elapsed_seconds = 0

        # Moving average estimated remaining time
        remaining_files = max(0, total_files - processed_count)
        estimated_remaining_seconds = None
        if processed_count > 0 and remaining_files > 0:
            avg_per_doc = elapsed_seconds / processed_count
            estimated_remaining_seconds = int(avg_per_doc * remaining_files)

        progress_pct = round((processed_count / total_files * 100.0), 1) if total_files > 0 else 0.0

        # Format timers
        def _fmt_seconds(sec: Optional[int]) -> str:
            if sec is None:
                return "Calculating..."
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        jobs_list = []
        total_batch_co2e_kg = 0.0
        for j in job_rows:
            j_dict = dict(j)
            val = j_dict.get("total_co2e_kg") or 0.0
            j_dict["total_kg_co2e"] = val
            total_batch_co2e_kg += val
            jobs_list.append(j_dict)

        return {
            "batch_id": batch_id,
            "status": status,
            "total_files": total_files,
            "total_documents": total_files,
            "processed_count": processed_count,
            "processed_documents": processed_count,
            "completed_count": completed_count,
            "review_count": review_count,
            "failed_count": failed_count,
            "queued_count": max(0, total_files - processed_count),
            "current_file": current_file,
            "progress_pct": progress_pct,
            "started_at": started_at_str,
            "completed_at": completed_at_str,
            "elapsed_seconds": elapsed_seconds,
            "elapsed_timer": _fmt_seconds(elapsed_seconds),
            "estimated_remaining_seconds": estimated_remaining_seconds,
            "estimated_remaining_timer": _fmt_seconds(estimated_remaining_seconds),
            "total_batch_co2e_kg": round(total_batch_co2e_kg, 2),
            "jobs": jobs_list
        }
