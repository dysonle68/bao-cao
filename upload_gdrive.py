import os
import sys
import subprocess

FOLDER_ID = '1WhdBEjeQAPWVbA33oixJtgB6hROC4RgJ'
FILE_PATH = r'D:\bao-cao\index.html'
FILE_NAME = 'Bao_Cao_Bang_Gia_San_Pham.html'

def install_and_import():
    print("Kiểm tra thư viện Google API...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib"])

def main():
    if not os.path.exists(FILE_PATH):
        print(f"Lỗi: Không tìm thấy file {FILE_PATH}")
        return

    print("--- HƯỚNG DẪN TẢI FILE LÊN GOOGLE DRIVE ---")
    print(f"Thư mục Google Drive mục tiêu: https://drive.google.com/drive/folders/{FOLDER_ID}")
    print(f"File local: {FILE_PATH}\n")

    try:
        install_and_import()
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        print("\nVui lòng chọn file credentials.json từ Google Cloud Console (nếu có OAuth client ID).")
        cred_path = input("Nhập đường dẫn đến client_secret.json (hoặc nhấn Enter để hủy): ").strip()
        
        if not cred_path or not os.path.exists(cred_path):
            print("\nKhông tìm thấy file credentials. Bạn có thể kéo thả file D:\\bao-cao\\index.html trực tiếp vào trình duyệt vừa mở.")
            return

        flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
        creds = flow.run_local_server(port=0)

        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': FILE_NAME,
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(FILE_PATH, mimetype='text/html')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print(f"\n✅ Upload thành công! File ID trên Google Drive: {file.get('id')}")

    except Exception as e:
        print(f"\nThông báo: {e}")
        print("\nĐể tải file lên Google Drive, bạn chỉ cần mở trình duyệt và kéo thả file index.html vào thư mục Google Drive.")

if __name__ == '__main__':
    main()
