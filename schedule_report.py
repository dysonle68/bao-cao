import time
import os
import subprocess
from datetime import datetime

def run_report():
    print(f"[{datetime.now()}] Bắt đầu tạo báo cáo index.html...")
    
    # Setup environment variables
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Run the report generator
    cmd = [
        "python", "-c",
        "import generate_monthly_report; generate_monthly_report.generate_report(month=None, output_file='index.html')"
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=r"D:\bao-cao",
            env=env,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] Cập nhật báo cáo thành công!")
            print(result.stdout)
            
            # Commit to git
            print(f"[{datetime.now()}] Pushing to Github...")
            subprocess.run(["git", "add", "index.html"], cwd=r"D:\bao-cao")
            subprocess.run(["git", "commit", "-m", "Auto-update index.html"], cwd=r"D:\bao-cao")
            subprocess.run(["git", "push"], cwd=r"D:\bao-cao")
        else:
            print(f"[{datetime.now()}] Có lỗi khi cập nhật báo cáo:")
            print(result.stderr)
            
    except Exception as e:
        print(f"[{datetime.now()}] Lỗi thực thi: {e}")

if __name__ == "__main__":
    print("Bắt đầu chương trình cập nhật tự động (Mỗi 2 tiếng)...")
    
    # Chạy lần đầu ngay lập tức
    run_report()
    
    # Lặp lại mỗi 2 tiếng (7200 giây)
    while True:
        print(f"[{datetime.now()}] Đang đợi 2 tiếng để chạy lần tiếp theo...")
        time.sleep(2 * 60 * 60)
        run_report()
