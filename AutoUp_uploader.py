# AutoUp_uploader.py - V3.0 with Multi-File Progress
# ProFTPD UTF-8 호환성 수정 버전

from AutoUp_ftp_utils import create_ftp_connection, create_ftp_folder, check_ftp_connection, reconnect_ftp
from AutoUp_upload_util import AutoBot_fileup_with_progress
from AutoUp_info_builder import build_info_json, save_info_json
from AutoUp_utils_loader import log_error
from AutoUp_env import WEBDOWN_DIR, TORRENT_DIR
import AutoUp_GUI
import os
import random
import time

gui_progress_callback = None

def set_gui_progress_callback(callback):
    """GUI 진행률 업데이트 콜백 설정"""
    global gui_progress_callback
    gui_progress_callback = callback

def sanitize_filename(filename):
    """
    FTP 업로드를 위한 파일명 정리 - 원본 방식
    - 특수문자만 제거하고 한글은 그대로 유지
    """
    return filename.replace(":", "").replace("?", "").replace("*", "").replace('"', "").replace("<", "").replace(">", "").replace("|", "").replace("'", "")

def generate_folder_name():
    t = time.strftime("%Y%m%d%H%M%S")
    r = str(random.randint(0, 999)).zfill(3)
    return t + r

def AutoUp_task(entry, ftp_name, upload_results):
    """업로드 태스크 - ProFTPD 호환"""
    thread_id = entry.get('thread_id', 0)
    thread_color = entry.get('thread_color', '#000000')
    
    if not entry.get("title"):
        log_error("❌ 오류: title이 비어 있음")
        return

    print(f"\n{'='*50}")
    print(f"🧕 업로드 작업 시작 (Thread #{thread_id})")
    print(f"   제목: {entry['title']}")
    print(f"   FTP: {ftp_name}")
    print(f"{'='*50}\n")

    # FTP 연결
    try:
        ftp = create_ftp_connection(ftp_name, timeout=10)
        print("✅ FTP 연결 성공")
    except Exception as e:
        log_error(f"❌ FTP 연결 실패: {e}")
        entry["status"] = "failed"
        entry["upload_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        upload_results.append(entry)
        return

    folder_name = generate_folder_name()
    print(f"📁 업로드 폴더: {folder_name}")
    
    try:
        remote_folder = create_ftp_folder(ftp, folder_name)
    except Exception as e:
        log_error(f"❌ 폴더 생성 실패: {e}")
        entry["status"] = "failed"
        upload_results.append(entry)
        try:
            ftp.quit()
        except:
            pass
        return

    uploaded_images = []
    uploaded_files = []
    upload_success = True
    
    # 이미지 업로드
    for image in entry.get("images", []):
        file_name = os.path.basename(image)
        print(f"📷 이미지: {file_name}")
        
        try:
            base, ext = os.path.splitext(file_name)
            sanitized_base = sanitize_filename(base)
            remote_path = f"/{folder_name}/{sanitized_base}.{ext.lstrip('.')}"
            
            with open(image, "rb") as f:
                result = ftp.storbinary(f"STOR {remote_path}", f)
                print(f"   ✅ 업로드 완료: {result}")
            
            uploaded_images.append(file_name)
        except Exception as e:
            print(f"   ❌ 업로드 실패: {e}")
            upload_success = False

    # 파일 업로드
    for file_path in entry.get("files", []):
        file_name = os.path.basename(file_path)
        print(f"📁 파일: {file_name}")
        
        if os.path.exists(file_path):
            base, ext = os.path.splitext(file_name)
            remote_fname = f"{sanitize_filename(base)}.{ext.lstrip('.')}"
            ftp_target_path = f"/{folder_name}/{remote_fname}"
            
            success = AutoBot_fileup_with_progress(
                ftp, file_path, ftp_target_path, file_name,
                uploaded_files, None, max_retries=2
            )
            
            if not success:
                upload_success = False
                print(f"   ❌ 업로드 실패")

    # info.json 생성
    if upload_success:
        print("\n📄 info.json 생성 중...")
        try:
            info_data = build_info_json(entry, uploaded_images, uploaded_files)
            save_info_json(ftp, info_data, remote_folder)
            print("   ✅ info.json 생성 완료")
        except Exception as e:
            print(f"   ❌ info.json 생성 실패: {e}")

    # 연결 종료
    try:
        ftp.quit()
        print("\n🔌 FTP 연결 종료")
    except:
        pass

    # 결과 저장
    entry["status"] = "success" if upload_success else "failed"
    entry["upload_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    entry["uploaded_images"] = uploaded_images
    entry["uploaded_files"] = uploaded_files
    entry["ftp_folder"] = folder_name
    upload_results.append(entry)

    if upload_success:
        print(f"🎉 업로드 완료: {entry['title']}\n")
    else:
        print(f"❌ 업로드 실패: {entry['title']}\n")
