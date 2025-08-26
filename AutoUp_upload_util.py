from AutoUp_env import TORRENT_DIR
import psutil
import os
import sys

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

def AutoBot_fileup(ftp, full_path, ftp_target_path, file, uploaded_files):
    try:
        with open(full_path, "rb") as f:
            ftp.storbinary(f"STOR {ftp_target_path}", f)
        print(f"✅ 파일 업로드 완료: {file}")
        uploaded_files.append(file)
    except Exception as e:
        log_error(f"❌ 파일 업로드 실패: {file} - {e}")

import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

import tkinter as tk
from tkinter import messagebox

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
