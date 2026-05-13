import os
import time
import hashlib
import requests
from datetime import datetime

class JediVCSMonitor:
    def __init__(self, workspace_path, api_url, api_key):
        self.workspace_path = workspace_path
        self.api_url = api_url
        self.api_key = api_key
        self.tracked_extensions = ['.pas', '.dfm', '.sql', '.pks', '.pkb']
        self.file_cache = {}

    def get_file_hash(self, filepath):
        """Calculate MD5 to detect changes"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def scan(self):
        """Scan workspace for changes in tracked files"""
        changes = []
        for root, dirs, files in os.walk(self.workspace_path):
            # Skip common junk dirs
            if 'bin' in root or 'lib' in root or '.git' in root:
                continue
                
            for file in files:
                if any(file.endswith(ext) for ext in self.tracked_extensions):
                    filepath = os.path.join(root, file)
                    try:
                        current_hash = self.get_file_hash(filepath)
                        if filepath not in self.file_cache:
                            self.file_cache[filepath] = current_hash
                            # Initial scan - don't count as change unless it's new
                        elif self.file_cache[filepath] != current_hash:
                            self.file_cache[filepath] = current_hash
                            changes.append({
                                'file': filepath,
                                'type': 'modified',
                                'timestamp': datetime.now().isoformat()
                            })
                    except Exception as e:
                        print(f"Error scanning {filepath}: {e}")
        return changes

    def run(self):
        print(f"Monitoring Jedi VCS at: {self.workspace_path}")
        # Initial population
        self.scan()
        
        while True:
            changes = self.scan()
            if changes:
                print(f"Detected {len(changes)} changes. Sending to cloud...")
                self.sync_changes(changes)
            time.sleep(5) # Polling interval

    def sync_changes(self, changes):
        """Send changes to cloud backend"""
        try:
            payload = {
                "machine_id": "local_dev_1", # Should be generated
                "changes": changes
            }
            # requests.post(f"{self.api_url}/agent/submit-analysis", json=payload, headers={"X-API-KEY": self.api_key})
            print(f"Synced: {payload}")
        except Exception as e:
            print(f"Sync failed: {e}")

if __name__ == "__main__":
    # Test stub
    monitor = JediVCSMonitor("C:/ERP_Source", "http://localhost:8000", "secret")
    # monitor.run()
