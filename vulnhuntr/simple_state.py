"""
Simple state manager for vulnhuntr analysis recovery.
Provides checkpoint/resume functionality using JSON file storage.
"""

import json
import hashlib
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class SimpleStateManager:
    """Simple state manager for analysis recovery"""
    
    def __init__(self, state_file: str = None):
        if state_file is None:
            state_file = os.getenv('VULNHUNTR_STATE_FILE', 'vulnhuntr_state.json')
        
        self.state_file = Path(state_file)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load state file {self.state_file}: {e}")
                # Backup corrupted file
                backup_file = self.state_file.with_suffix('.backup')
                if self.state_file.exists():
                    self.state_file.rename(backup_file)
                    print(f"Corrupted state file backed up to {backup_file}")
        
        return {
            "sessions": {},
            "completed_files": {},
            "version": "1.0"
        }
    
    def _save_state(self):
        """Save state to file"""
        try:
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.state_file)
        except IOError as e:
            print(f"Warning: Could not save state file: {e}")
    
    def _generate_session_id(self, repo_path: str) -> str:
        """Generate unique session ID"""
        timestamp = str(time.time())
        content = f"{repo_path}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash for file (path + modification time)"""
        try:
            path_obj = Path(file_path)
            if path_obj.exists():
                mtime = path_obj.stat().st_mtime
                content = f"{file_path}_{mtime}"
            else:
                content = file_path
            return hashlib.md5(content.encode()).hexdigest()
        except OSError:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def start_session(self, repo_path: str, files: List[str]) -> str:
        """Start new analysis session"""
        session_id = self._generate_session_id(repo_path)
        
        self.state["sessions"][session_id] = {
            "repo_path": repo_path,
            "started_at": time.time(),
            "total_files": len(files),
            "completed_files": 0,
            "files": files,
            "status": "running",
            "last_updated": time.time()
        }
        self._save_state()
        return session_id
    
    def mark_file_completed(self, session_id: str, file_path: str, result: Any):
        """Mark file as completed with result"""
        file_hash = self._calculate_file_hash(file_path)
        
        # Save result for caching
        self.state["completed_files"][file_hash] = {
            "file_path": file_path,
            "result": result,
            "completed_at": time.time(),
            "session_id": session_id
        }
        
        # Update session progress
        if session_id in self.state["sessions"]:
            self.state["sessions"][session_id]["completed_files"] += 1
            self.state["sessions"][session_id]["last_updated"] = time.time()
        
        self._save_state()
    
    def mark_file_failed(self, session_id: str, file_path: str, error: str):
        """Mark file as failed with error details"""
        file_hash = self._calculate_file_hash(file_path)
        
        # Save error for tracking
        self.state["completed_files"][file_hash] = {
            "file_path": file_path,
            "error": error,
            "failed_at": time.time(),
            "session_id": session_id,
            "status": "failed"
        }
        
        # Update session progress (count failed files as completed for progress tracking)
        if session_id in self.state["sessions"]:
            self.state["sessions"][session_id]["completed_files"] += 1
            self.state["sessions"][session_id]["last_updated"] = time.time()
        
        self._save_state()
    
    def get_cached_result(self, file_path: str) -> Optional[Any]:
        """Get cached result for file"""
        file_hash = self._calculate_file_hash(file_path)
        cached = self.state["completed_files"].get(file_hash)
        
        if cached and "result" in cached:
            # Check if this is a valid result (not an error)
            if cached.get("status") != "failed":
                return cached["result"]
        
        return None
    
    def is_file_failed(self, file_path: str) -> bool:
        """Check if file previously failed"""
        file_hash = self._calculate_file_hash(file_path)
        cached = self.state["completed_files"].get(file_hash)
        return cached is not None and cached.get("status") == "failed"
    
    def get_pending_files(self, session_id: str) -> List[str]:
        """Get list of files not yet completed in session"""
        if session_id not in self.state["sessions"]:
            return []
        
        session = self.state["sessions"][session_id]
        all_files = session["files"]
        
        pending = []
        for file_path in all_files:
            file_hash = self._calculate_file_hash(file_path)
            if file_hash not in self.state["completed_files"]:
                pending.append(file_path)
        
        return pending
    
    def complete_session(self, session_id: str):
        """Mark session as completed"""
        if session_id in self.state["sessions"]:
            self.state["sessions"][session_id]["status"] = "completed"
            self.state["sessions"][session_id]["completed_at"] = time.time()
            self.state["sessions"][session_id]["last_updated"] = time.time()
            self._save_state()
    
    def fail_session(self, session_id: str, error: str = ""):
        """Mark session as failed"""
        if session_id in self.state["sessions"]:
            self.state["sessions"][session_id]["status"] = "failed"
            self.state["sessions"][session_id]["error"] = error
            self.state["sessions"][session_id]["failed_at"] = time.time()
            self.state["sessions"][session_id]["last_updated"] = time.time()
            self._save_state()
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        return self.state["sessions"].get(session_id)
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions with summary information"""
        sessions = []
        for sid, session in self.state["sessions"].items():
            sessions.append({
                "id": sid,
                "repo_path": session["repo_path"],
                "status": session["status"],
                "progress": f"{session['completed_files']}/{session['total_files']}",
                "started_at": session["started_at"],
                "last_updated": session.get("last_updated", session["started_at"])
            })
        
        # Sort by last updated (most recent first)
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up sessions older than specified days"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        sessions_to_remove = []
        for sid, session in self.state["sessions"].items():
            if session.get("last_updated", session["started_at"]) < cutoff_time:
                sessions_to_remove.append(sid)
        
        for sid in sessions_to_remove:
            del self.state["sessions"][sid]
        
        # Also cleanup old completed files
        files_to_remove = []
        for file_hash, file_info in self.state["completed_files"].items():
            completed_at = file_info.get("completed_at") or file_info.get("failed_at", 0)
            if completed_at < cutoff_time:
                files_to_remove.append(file_hash)
        
        for file_hash in files_to_remove:
            del self.state["completed_files"][file_hash]
        
        if sessions_to_remove or files_to_remove:
            self._save_state()
            print(f"Cleaned up {len(sessions_to_remove)} old sessions and {len(files_to_remove)} old file records")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_sessions = len(self.state["sessions"])
        completed_sessions = sum(1 for s in self.state["sessions"].values() if s["status"] == "completed")
        running_sessions = sum(1 for s in self.state["sessions"].values() if s["status"] == "running")
        failed_sessions = sum(1 for s in self.state["sessions"].values() if s["status"] == "failed")
        
        total_files = len(self.state["completed_files"])
        successful_files = sum(1 for f in self.state["completed_files"].values() if f.get("status") != "failed")
        failed_files = sum(1 for f in self.state["completed_files"].values() if f.get("status") == "failed")
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "running_sessions": running_sessions,
            "failed_sessions": failed_sessions,
            "total_files_processed": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "cache_hit_rate": f"{(successful_files / max(total_files, 1)) * 100:.1f}%" if total_files > 0 else "0%"
        }