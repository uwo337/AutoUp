from ftplib import FTP
from AutoUp_env import ftp_configs

def create_ftp_connection(ftp_name):
    config = ftp_configs[ftp_name]
    print("🔌 FTP 연결 시도 중...")
    ftp = FTP()
    ftp.connect(config["host"], int(config["port"]))
    ftp.login(config["user"], config["password"])
    print(f"✅ FTP 연결 성공 ({ftp.host})") 
    return ftp

def create_ftp_folder(ftp, path):
    """
    🔹 FTP 경로 상의 폴더를 생성
    """
    # print(f"📁 FTP 폴더 생성 시작: {path}")
    for part in path.strip("/").split("/"):
        try:
            ftp.cwd(part)
            # print(f"📂 이미 존재하는 폴더: {part}")
        except Exception:
            try:
                ftp.mkd(part)
                ftp.cwd(part)
                # print(f"➕ 폴더 생성됨: {part}")
            except Exception as e:
                print(f"❌ 폴더 생성 실패: {part}, 오류: {e}")
                raise e
    return path

def upload_file(ftp, local_path, remote_path):
    """
    🔹 파일을 FTP 서버에 업로드
    """
    # print(f"📤 파일 업로드 시도: {local_path} → {remote_path}")
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)
    print("✅ 업로드 완료")

