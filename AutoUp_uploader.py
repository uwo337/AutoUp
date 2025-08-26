from AutoUp_ftp_utils import create_ftp_connection, create_ftp_folder
from AutoUp_upload_util import AutoBot_fileup
from AutoUp_info_builder import build_info_json, save_info_json
from AutoUp_utils_loader import log_error
from AutoUp_env import WEBDOWN_DIR, TORRENT_DIR
import os
import random
import time

def sanitize_filename(filename):
    return filename.replace(":", "").replace("?", "").replace("*", "").replace('"', "").replace("<", "").replace(">", "").replace("|", "").replace("'", "")

def generate_folder_name():
    t = time.strftime("%Y%m%d%H%M%S")
    r = str(random.randint(0, 999)).zfill(3)
    return t + r

def AutoUp_task(entry, ftp_name, upload_results):
    if not entry.get("title"):
        log_error("❌ 오류: title이 비어 있어 업로드를 건너뜁니다.")
        return

    # print(f"🧕 새로운 업로드 쓰레드 시작: title = {entry['title']}")
    # print(f"🧕 선택된 FTP: {ftp_name}")

    ftp = create_ftp_connection(ftp_name)
    # print("✅ FTP 연결 성공")

    folder_name = generate_folder_name()
    remote_folder = create_ftp_folder(ftp, folder_name)
    # print(f"📂 FTP 폴더 생성됨: {remote_folder}")

    uploaded_images = []
    uploaded_files = []

    for image in entry.get("images", []):
        local_path = image  # ✅ 경로 그대로 사용
        base, ext = os.path.splitext(os.path.basename(image))
        remote_path = f"/{remote_folder}/{sanitize_filename(base)}.{ext.lstrip('.')}"
        # print(f"🖼 이미지 업로드 시작: {os.path.basename(image)}")
        # print(f"✅ remote_path : {remote_path}")
        # print(f"✅ local_path : {local_path}")
        try:
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"✅ 이미지 업로드 완료: {os.path.basename(image)}")
            uploaded_images.append(os.path.basename(image))
        except Exception as e:
            log_error(f"❌ 이미지 업로드 실패: {local_path} - {e}")

    file_list = entry.get("files", [])
    count = len(file_list)
    upload_success = True
    for i in range(count):
        try:
            full_path = file_list[i]  # ✅ 절대경로
            file = os.path.basename(full_path)  # ✅ 반드시 필요!

            # print(f"✅ full_path : {full_path}")
            # print(f"📄 자료파일 업로드 시작: {file}")

            base, ext = os.path.splitext(file)
            remote_fname = f"{sanitize_filename(base)}.{ext.lstrip('.')}"
            ftp_target_path = f"/{remote_folder}/{remote_fname}"

            # print(f"✅ ftp_target_path : {ftp_target_path}")
            # print(f"✅ local_path : {full_path}")

            if os.path.exists(full_path):
                AutoBot_fileup(ftp, full_path, ftp_target_path, file, uploaded_files)
            else:
                log_error(f"❌ 자료 파일 없음: {full_path}")
                upload_success = False
        except Exception as e:
            print(f"❌ {i}번째 파일 처리 중 오류: {e}")
            upload_success = False

    if upload_success:
        info_data = build_info_json(entry)
        json_remote_path = "info.json"
        save_info_json(info_data, ftp, json_remote_path)
        # print("📄 info.json 생성 완료")
    else:
        print("🚫 일부 파일 업로드 실패로 info.json 생성 생략됨")

    ftp.quit()

    # ✅ 결과 기록 추가
    entry["status"] = "success" if upload_success else "failed"
    entry["upload_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    entry["error_message"] = ""

    upload_results.append(entry)

