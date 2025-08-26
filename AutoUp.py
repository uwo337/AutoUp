# AutoUp_autobot.py (PID 파일 기반 중복실행 체크)

import os
import sys
import threading
import time
import json
import tempfile
import tkinter as tk
from tkinter import messagebox
from queue import Queue
from AutoUp_uploader import AutoUp_task
import AutoUp_GUI
import AutoUp_env
from AutoUp_env import ftp_configs, NETWORK_DELAY

# ===== 설정 부분 =====
PROGRAM_ID = "AutoUp"  # 각 프로그램마다 다르게 설정: "AutoUp", "AutoDown", "AutoSync" 등

# ✅ 전역 변수
upload_queue = Queue()
lock_file_path = None

# ✅ PID 파일 기반 중복실행 체크 (포트 사용 안함)
def check_already_running():
    global lock_file_path
    
    # 임시 디렉토리에 프로그램별 고유 PID 파일 생성
    temp_dir = tempfile.gettempdir()
    lock_file_path = os.path.join(temp_dir, f"{PROGRAM_ID}_instance.pid")
    
    try:
        current_pid = os.getpid()
        
        print(f"🔍 {PROGRAM_ID} 중복실행 체크 (PID 파일 방식)")
        print(f"🔍 PID 파일 경로: {lock_file_path}")
        print(f"🔍 현재 PID: {current_pid}")
        
        # 기존 PID 파일이 있는지 체크
        if os.path.exists(lock_file_path):
            with open(lock_file_path, 'r') as f:
                try:
                    stored_pid = int(f.read().strip())
                    print(f"🔍 기존 PID 파일 발견: {stored_pid}")
                    
                    # 해당 PID의 프로세스가 실제로 존재하는지 체크
                    if is_process_running(stored_pid):
                        print(f"❌ {PROGRAM_ID}이 이미 실행중입니다 (PID: {stored_pid})")
                        show_duplicate_warning()
                        return True
                    else:
                        print(f"🔄 기존 PID {stored_pid}는 이미 종료됨 - 파일 업데이트")
                        
                except (ValueError, IOError) as e:
                    print(f"⚠️ PID 파일 손상됨: {e} - 새로 생성")
        
        # 현재 PID를 파일에 저장
        with open(lock_file_path, 'w') as f:
            f.write(str(current_pid))
        
        print(f"✅ {PROGRAM_ID} - PID 파일 생성 완료")
        return False  # 중복 실행 아님
        
    except Exception as e:
        print(f"⚠️ PID 파일 체크 실패: {e}")
        return False  # 에러 시 실행 허용

def is_process_running(pid):
    """PID로 프로세스 실행 상태 체크 (크로스 플랫폼)"""
    try:
        if os.name == 'nt':  # Windows
            import subprocess
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                  capture_output=True, text=True, timeout=5)
            return str(pid) in result.stdout
        else:  # Unix/Linux/Mac
            os.kill(pid, 0)  # 시그널 0 - 프로세스 존재 체크만
            return True
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False

def show_duplicate_warning():
    """중복 실행 경고 메시지"""
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        f"{PROGRAM_ID} - 중복 실행", 
        f"{PROGRAM_ID} 프로그램이 이미 실행중입니다.\n\n"
        f"기존 프로그램을 종료한 후 다시 실행해주세요."
    )
    root.destroy()

# ✅ Named Pipe 서버 루프 (기존과 동일)
def start_named_pipe_server():
    try:
        import win32pipe, win32file, pywintypes
        
        PIPE_NAME = r'\\.\\pipe\\MySimplePipe'
        print(f"Named Pipe 서버 시작: {PIPE_NAME}")
        
        pipe = win32pipe.CreateNamedPipe(
            PIPE_NAME,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536, 0, None
        )
        
        while True:
            print("⌛ 클라이언트 연결 대기 중...")
            try:
                win32pipe.ConnectNamedPipe(pipe, None)
            except pywintypes.error as e:
                if e.winerror == 535:  # ERROR_PIPE_CONNECTED
                    print("⚠️ 이미 연결된 파이프 (연결 유지)")
                else:
                    print(f"❌ ConnectNamedPipe 오류: {e}")
                    continue

            print("✅ 클라이언트 연결됨")

            try:
                result, data = win32file.ReadFile(pipe, 64 * 1024)
                message = data.decode('utf-8')

                try:
                    json_data = json.loads(message)
                    upload_queue.put(json_data)
                    response = json.dumps({"status": "received"})
                except json.JSONDecodeError:
                    response = json.dumps({"status": "error", "message": "Invalid JSON"})

                win32file.WriteFile(pipe, response.encode('utf-8'))

            except Exception as e:
                print(f"❌ Pipe 처리 오류: {e}")

            finally:
                win32pipe.DisconnectNamedPipe(pipe)
                
    except ImportError:
        print("❌ pywin32 모듈이 없어서 Named Pipe 서버를 시작할 수 없습니다.")
        print("   pip install pywin32 로 설치하거나 다른 통신 방법을 사용하세요.")

# ✅ 업로드 모니터링 루프
def monitor_and_upload():
    global upload_results
    loop_delay = 1
    AutoUp_env.selected_ftp_name = "FTP1"

    while True:
        if not upload_queue.empty():
            task = upload_queue.get()
            print(f"\n🥕 새로운 업로드 스레드 시작: title = {task.get('title', 'N/A')}")
            thread = threading.Thread(target=AutoUp_task, args=(task, AutoUp_env.selected_ftp_name, upload_results))
            thread.start()
        time.sleep(loop_delay)

# ✅ 정리 함수 (프로그램 종료 시)
def cleanup_on_exit():
    global lock_file_path
    
    # PID 파일 정리
    if lock_file_path and os.path.exists(lock_file_path):
        try:
            os.remove(lock_file_path)
            print(f"✅ {PROGRAM_ID} - PID 파일 정리 완료")
        except Exception as e:
            print(f"⚠️ PID 파일 정리 실패: {e}")

# ✅ 메인 진입점
if __name__ == "__main__":
    # PID 파일 기반 중복실행 체크 (포트 사용 안함)
    if check_already_running():
        sys.exit()
    
    try:
        # Named Pipe 서버 시작 (pywin32 있는 경우만)
        pipe_thread = threading.Thread(target=start_named_pipe_server, daemon=True)
        pipe_thread.start()

        # 업로드 모니터링 시작
        monitor_thread = threading.Thread(target=monitor_and_upload, daemon=True)
        monitor_thread.start()

        upload_results = []
        
        # 프로그램 종료 시 정리
        import atexit
        atexit.register(cleanup_on_exit)
        
        # GUI 시작
        AutoUp_GUI.AutoUp_GUI(upload_results, NETWORK_DELAY)

    except Exception as e:
        cleanup_on_exit()
        import tkinter.messagebox as msgbox
        msgbox.showerror("오류", f"오류가 발생했습니다:\n{e}")
        sys.exit(1)