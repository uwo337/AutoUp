# 개선된 AutoUp_upload_util.py - V2.3 Clean Exception Handling
# 대용량 파일 업로드 지원 개선 - 깔끔한 예외 처리

from AutoUp_env import TORRENT_DIR
import psutil
import os
import sys
import socket
import time
import threading
import tkinter as tk
from tkinter import messagebox

# 멀티스레드 출력 동기화용 락
print_lock = threading.Lock()

# 커스텀 예외 클래스 정의
class UploadStuckError(Exception):
    """업로드 멈춤 감지"""
    pass

class UploadIncompleteError(Exception):
    """불완전한 업로드"""
    pass

def AutoUp_upload_order(entry):
    """
    🔹 entry["files"] 목록(전체 경로)을 파일 크기 기준으로 정렬
    🔹 가장 큰 파일의 인덱스와 크기를 함께 반환
    🔸 반환값: (정렬된 전체경로 리스트, 최대 인덱스, 최대 크기)
    """
    print(f"📦  AutoUp_upload_order함수 진입구") 
    file_sizes = [(f, os.path.getsize(f)) for f in entry.get("files", []) if os.path.exists(f)]
    if not file_sizes:
        print("❌ AutoUp_upload_order: 유효한 파일이 없습니다.")
        return [], -1, -1

    file_sizes.sort(key=lambda x: x[1])
    ordered_files = [f for f, _ in file_sizes]
    max_index = len(ordered_files) - 1
    max_size = file_sizes[-1][1]

    print(f"📦 AutoUp_upload_order 결과 → ordered_files: {ordered_files}, max_index: {max_index}, max_size: {max_size}")
    return ordered_files, max_index, max_size

def AutoBot_fileup(ftp, full_path, ftp_target_path, file, uploaded_files, max_retries=3):
    """
    기본 FTP 파일 업로드 함수 (진행률 표시 없음)
    """
    return AutoBot_fileup_with_progress(ftp, full_path, ftp_target_path, file, 
                                       uploaded_files, None, max_retries)

def calculate_timeout(file_size):
    """
    파일 크기 기반 타임아웃 계산 (최소 속도 100KB/s 기준)
    """
    min_speed = 100 * 1024  # 100KB/s
    base_timeout = (file_size / min_speed) * 1.5  # 1.5배 여유
    return max(300, min(base_timeout, 7200))  # 최소 5분, 최대 2시간

def check_upload_status(ftp, ftp_target_path, file_size, uploaded_bytes, thread_id):
    """
    업로드 상태 체크 - 깔끔한 예외 처리
    
    Returns:
        tuple: (status, percent, remote_size)
        - status: "completed", "in_progress", "error"
        - percent: 진행률 (0-100)
        - remote_size: 원격 파일 크기 (None if error)
    """
    
    # 1. 로컬 업로드 상태 확인 (최우선)
    local_percent = (uploaded_bytes[0] / file_size) * 100 if file_size > 0 else 100
    
    if uploaded_bytes[0] >= file_size * 0.999:
        return "completed", local_percent, None
    
    # 2. 원격 파일 크기 확인 시도
    try:
        # 연결 테스트
        temp_timeout = ftp.timeout
        ftp.timeout = 5
        
        try:
            ftp.voidcmd("NOOP")
            
            # SIZE 명령 실행
            remote_size = ftp.size(ftp_target_path)
            remote_percent = (remote_size / file_size) * 100 if file_size > 0 else 0
            
            if remote_size >= file_size * 0.999:
                return "completed", remote_percent, remote_size
            else:
                return "in_progress", remote_percent, remote_size
                
        finally:
            ftp.timeout = temp_timeout
            
    except (socket.error, OSError, Exception) as e:
        # SIZE 실패해도 로컬 상태로 판단
        if uploaded_bytes[0] >= file_size * 0.999:
            return "completed", local_percent, None
        else:
            return "error", local_percent, None

def monitor_large_upload(ftp, ftp_target_path, file_size, uploaded_bytes, 
                         upload_complete, upload_thread, thread_id, progress_callback=None):
    """
    90% 이후 모니터링 - 단순화된 로직
    
    Returns:
        bool: 업로드 성공 여부
    """
    
    last_size = 0
    no_change_count = 0
    max_no_change = 3  # 45초 (15초 * 3)
    
    with print_lock:
        print(f"   [T{thread_id:02d}] 🔍 90% 이후 모니터링 시작")
        sys.stdout.flush()
    
    while not upload_complete.is_set():
        time.sleep(15)
        
        # 업로드 완료 체크
        if upload_complete.is_set():
            return True
            
        # 상태 체크 (예외 처리 함수로 위임)
        status, percent, remote_size = check_upload_status(
            ftp, ftp_target_path, file_size, uploaded_bytes, thread_id
        )
        
        # 상태별 처리
        if status == "completed":
            with print_lock:
                print(f"   [T{thread_id:02d}] ✅ 업로드 완료 확인: {percent:.1f}%")
                sys.stdout.flush()
            return True
            
        elif status == "in_progress":
            with print_lock:
                print(f"   [T{thread_id:02d}] 📊 진행중: {percent:.1f}% ({remote_size}/{file_size} bytes)")
                sys.stdout.flush()
            
            # 멈춤 감지 (99% 미만에서만)
            if remote_size == last_size:
                no_change_count += 1
                if no_change_count >= max_no_change and percent < 99:
                    with print_lock:
                        print(f"   [T{thread_id:02d}] ❌ 멈춤 감지: {percent:.1f}% - {no_change_count*15}초간 변화 없음")
                        sys.stdout.flush()
                    return False
            else:
                no_change_count = 0
                last_size = remote_size
                
        elif status == "error":
            # 오류지만 계속 대기
            with print_lock:
                print(f"   [T{thread_id:02d}] ⚠️ 체크 실패 (로컬 {percent:.1f}%), 계속 대기중...")
                sys.stdout.flush()
    
    return True

def AutoBot_fileup_with_progress(ftp, full_path, ftp_target_path, file, 
                                uploaded_files, progress_callback=None, max_retries=3):
    """
    개선된 FTP 파일 업로드 함수 - V3.1 UTF-8 Safe
    - 대용량 파일 지원
    - 재시도 메커니즘
    - 타임아웃 문제 해결
    - 깔끔한 콘솔 출력 (10% 단위)
    - UTF-8 인코딩 안전 처리
    """
    # 현재 스레드 ID 가져오기
    thread_id = threading.current_thread().ident % 100  # 2자리로 축약
    if not os.path.exists(full_path):
        log_error(f"❌ 파일이 존재하지 않음: {full_path}")
        return False
        
    file_size = os.path.getsize(full_path)
    
    # 파일 크기에 따른 버퍼 크기 조정 (효율 개선)
    if file_size < 10 * 1024 * 1024:  # 10MB 미만
        buffer_size = 32768  # 32KB (기존 8KB)
    elif file_size < 100 * 1024 * 1024:  # 100MB 미만
        buffer_size = 131072  # 128KB (기존 32KB)
    elif file_size < 500 * 1024 * 1024:  # 500MB 미만
        buffer_size = 262144  # 256KB (기존 64KB)
    else:  # 500MB 이상
        buffer_size = 524288  # 512KB (기존 256KB)
    
    print(f"📊 파일: {file}")
    print(f"   크기: {file_size:,} bytes ({file_size/(1024*1024):.1f} MB)")
    print(f"   버퍼: {buffer_size:,} bytes")
    
    # GUI 진행률 초기화
    if progress_callback:
        try:
            progress_callback(file, 0, "uploading")
        except:
            pass
    
    for attempt in range(max_retries):
        try:
            # FTP 연결 상태 확인
            try:
                ftp.voidcmd("NOOP")  # Keep-alive 명령
            except Exception as e:
                print(f"⚠️ FTP 연결 상태 확인 실패: {e}")
                return False
            
            # 파일 크기에 따른 타임아웃 설정
            original_timeout = ftp.timeout
            calculated_timeout = calculate_timeout(file_size)
            print(f"   🔧 타임아웃 설정: {calculated_timeout:.0f}초 (파일 {file_size/(1024*1024):.1f}MB)")
            ftp.timeout = calculated_timeout
            
            try:
                # 업로드 진행 상황 추적을 위한 변수
                uploaded_bytes = [0]
                last_print_milestone = [0]  # 마지막으로 출력한 마일스톤 (10% 단위)
                last_gui_update = [time.time()]
                last_gui_percent = [0]
                
                def callback(data):
                    uploaded_bytes[0] += len(data)
                    
                    # 업데이트 주기 검사 (10MB마다 또는 2초마다)
                    update_interval = 10 * 1024 * 1024  # 10MB
                    current_time = time.time()
                    
                    if (uploaded_bytes[0] % update_interval < len(data) or 
                        current_time - last_gui_update[0] >= 2.0):  # 0.5초→2초
                        
                        percent = (uploaded_bytes[0] / file_size) * 100 if file_size > 0 else 100
                        
                        # 콘솔 출력 개선 (10% 단위로만, 95%까지만)
                        current_milestone = min(int(percent / 10) * 10, 95)  # 최대 95%까지만 표시
                        if current_milestone > last_print_milestone[0]:
                            mb_uploaded = uploaded_bytes[0] / (1024 * 1024)
                            mb_total = file_size / (1024 * 1024)
                            
                            # 스레드 ID 및 파일 정보 포함
                            short_name = file if len(file) <= 25 else file[:22] + "..."
                            
                            with print_lock:
                                print(f"   [T{thread_id:02d}] → {current_milestone:3}% ({mb_uploaded:6.1f}/{mb_total:6.1f} MB) | {short_name}")
                                
                                # ✅ 로그 출력과 동시에 GUI 업데이트 (동기화)
                                if progress_callback:
                                    try:
                                        progress_callback(file, current_milestone, "uploading")
                                        last_gui_update[0] = current_time
                                        last_gui_percent[0] = current_milestone
                                    except:
                                        pass
                                
                                sys.stdout.flush()
                            
                            last_print_milestone[0] = current_milestone
                    
                    return data
                
                # 실제 업로드 수행
                start_time = time.time()
                
                with open(full_path, "rb") as f:
                    # 이어받기 시도 (재시도인 경우)
                    resume_position = 0
                    if attempt > 0:
                        try:
                            ftp.voidcmd("TYPE I")  # Binary 모드 설정
                            try:
                                # 이미 업로드된 크기 확인
                                size = ftp.size(ftp_target_path)
                                if size and size > 0 and size < file_size:
                                    resume_percent = int((size / file_size) * 100)
                                    print(f"🔄 이어받기: {resume_percent}%부터 재개 ({size:,} bytes)")
                                    f.seek(size)
                                    uploaded_bytes[0] = size
                                    resume_position = size
                                    last_print_milestone[0] = int(resume_percent / 10) * 10
                                    ftp.voidcmd(f"REST {size}")
                                    
                                    # GUI 진행률 업데이트
                                    if progress_callback:
                                        progress_callback(file, resume_percent, "uploading")
                            except:
                                pass  # 이어받기 실패 시 처음부터
                        except:
                            pass
                    
                    # 업로드 실행
                    print(f"📤 업로드 시작...")
                    
                    # STOR 명령을 별도 스레드로 실행 (90% 이후 모니터링)
                    upload_complete = threading.Event()
                    upload_result = [None]
                    
                    def upload_thread_func():
                        try:
                            upload_result[0] = ftp.storbinary(f"STOR {ftp_target_path}", f, blocksize=buffer_size, callback=callback)
                        except Exception as e:
                            upload_result[0] = e
                        finally:
                            upload_complete.set()
                    
                    upload_thread = threading.Thread(target=upload_thread_func)
                    upload_thread.start()
                    
                    # 90% 도달까지 대기
                    while uploaded_bytes[0] < file_size * 0.9 and not upload_complete.is_set():
                        time.sleep(1)
                    
                    # 90% 이상에서 모니터링 시작
                    if uploaded_bytes[0] >= file_size * 0.9 and not upload_complete.is_set():
                        success = monitor_large_upload(
                            ftp, ftp_target_path, file_size, uploaded_bytes,
                            upload_complete, upload_thread, thread_id, progress_callback
                        )
                        
                        if not success:
                            upload_thread.join(timeout=5)
                            raise UploadStuckError(f"Upload stuck at {(uploaded_bytes[0]/file_size)*100:.1f}%")
                    
                    # 스레드 완료 대기
                    upload_thread.join(timeout=30)
                    
                    # 결과 확인
                    if isinstance(upload_result[0], Exception):
                        raise upload_result[0]
                    else:
                        result = upload_result[0]
                    
                    # 결과 확인
                    if "226" in str(result) or "complete" in str(result).lower():
                        # 정상 완료
                        pass
                    else:
                        # 비정상 종료 시 SIZE로 확인
                        with print_lock:
                            print(f"   [T{thread_id:02d}] 파일 크기 확인 중...")
                            sys.stdout.flush()
                        
                        temp_timeout = ftp.timeout
                        ftp.timeout = 10
                        try:
                            remote_size = ftp.size(ftp_target_path)
                            if remote_size >= file_size * 0.99:
                                with print_lock:
                                    print(f"   [T{thread_id:02d}] ✅ 파일 전송 확인 ({remote_size}/{file_size} bytes)")
                                    sys.stdout.flush()
                            else:
                                with print_lock:
                                    print(f"   [T{thread_id:02d}] ⚠️ 불완전 전송 ({remote_size}/{file_size} bytes)")
                                    sys.stdout.flush()
                                raise UploadIncompleteError(f"Incomplete upload: {remote_size}/{file_size} bytes")
                        except UploadIncompleteError:
                            raise
                        except:
                            # SIZE 명령 실패는 무시
                            pass
                        finally:
                            ftp.timeout = temp_timeout
                    
                # 마지막 100% 진행률 표시 (로그와 GUI 동시에)
                if last_print_milestone[0] < 100:
                    with print_lock:
                        mb_total = file_size / (1024 * 1024)
                        print(f"   [T{thread_id:02d}] → 100% ({mb_total:6.1f}/{mb_total:6.1f} MB) | {file[:25] if len(file) <= 25 else file[:22] + '...'}")
                        
                        # ✅ 100% 완료 시 GUI도 함께 업데이트
                        if progress_callback:
                            try:
                                progress_callback(file, 100, "uploading")
                            except:
                                pass
                        
                        sys.stdout.flush()
                
                elapsed_time = time.time() - start_time
                actual_uploaded = file_size - resume_position
                speed = (actual_uploaded / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
                
                with print_lock:
                    print(f"[T{thread_id:02d}] ✅ 업로드 완료: {file} ({elapsed_time:.1f}초, {speed:.1f} MB/s)")
                    sys.stdout.flush()
                
                uploaded_files.append(file)
                
                # GUI 완료 상태로 변경 (진행률은 이미 100% 표시됨)
                if progress_callback:
                    try:
                        progress_callback(file, 100, "completed")  # 상태만 변경
                    except:
                        pass
                
                return True
                
            finally:
                # 타임아웃 복원
                ftp.timeout = original_timeout
                
        except socket.timeout as e:
            current_percent = int((uploaded_bytes[0] / file_size) * 100) if file_size > 0 else 0
            with print_lock:
                print(f"❌ 타임아웃 (시도 {attempt + 1}/{max_retries}) - 진행률: {current_percent}%")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                with print_lock:
                    print(f"⏳ {wait_time}초 후 재시도...")
                time.sleep(wait_time)
                # FTP 연결은 재사용하지 않고 실패 처리
                return False
            else:
                log_error(f"❌ 최종 업로드 실패 (타임아웃): {file}")
                if progress_callback:
                    progress_callback(file, 0, "failed")
                return False
                
        except UploadStuckError as e:
            with print_lock:
                print(f"❌ 업로드 멈춤 감지 (시도 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                with print_lock:
                    print(f"⏳ {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                log_error(f"❌ 최종 업로드 실패 (멈춤): {file}")
                if progress_callback:
                    progress_callback(file, 0, "failed")
                return False
                
        except UploadIncompleteError as e:
            with print_lock:
                print(f"❌ 불완전한 업로드 (시도 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                with print_lock:
                    print(f"⏳ {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                log_error(f"❌ 최종 업로드 실패 (불완전): {file}")
                if progress_callback:
                    progress_callback(file, 0, "failed")
                return False
                
        except Exception as e:
            with print_lock:
                print(f"❌ 업로드 실패 (시도 {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                with print_lock:
                    print(f"⏳ {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                log_error(f"❌ 최종 업로드 실패: {file} - {e}")
                if progress_callback:
                    progress_callback(file, 0, "failed")
                return False
    
    return False

def log_error(message):
    """에러 로깅 함수"""
    print(message)
    # 파일로 로깅 추가
    try:
        with open("AutoUp_error.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def is_already_running(process_name):
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['pid'] == current_pid:
            continue
        cmdline = proc.info.get('cmdline')
        if cmdline and process_name in ' '.join(cmdline):
            show_popup("⚠️ 프로그램이 이미 실행 중입니다.")
            return True
    return False

def show_popup(message):
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    messagebox.showwarning("중복 실행 감지", message)
    root.destroy()