import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DataFileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_run = 0
        
    def should_run(self):
        # Debounce to prevent multiple rapid triggers (e.g. from save operations)
        current_time = time.time()
        if current_time - self.last_run > 5:
            self.last_run = current_time
            return True
        return False

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            if self.should_run():
                print(f"Detected modification in: {event.src_path}")
                self.run_update()
            
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            if self.should_run():
                print(f"Detected new file: {event.src_path}")
                self.run_update()
            
    def run_update(self):
        print("Running update_report.py...")
        # Add a small delay to ensure the file is fully written/copied before reading
        time.sleep(2)
        try:
            # Run the report generator
            subprocess.run(["python", "-X", "utf8", "update_report.py"], check=True)
            print("Successfully generated new index.html")
            
            # Commit and push to GitHub
            print("Committing and pushing to GitHub...")
            subprocess.run(["git", "add", "index.html", "data/"], check=True)
            
            # Check if there are changes to commit
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if status.stdout.strip():
                subprocess.run(["git", "commit", "-m", "Auto-update report data and HTML from local script"], check=True)
                subprocess.run(["git", "push"], check=True)
                print("Successfully pushed changes to GitHub.")
            else:
                print("No changes to commit.")
                
        except subprocess.CalledProcessError as e:
            print(f"Error during auto-update process: {e}")

if __name__ == "__main__":
    path = r"D:\bao-cao\data"
    
    # Create data directory if it doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
        
    event_handler = DataFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Watching for Excel files in {path}...\nPress Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
