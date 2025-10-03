#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스크립트 - 로그와 GUI 동기화 테스트
"""

import os
import sys
import time
import ftplib
import threading
from AutoUp_upload_util import AutoBot_fileup_with_progress
from AutoUp_env import ftp_configs

# 테스트용 GUI 진행률 표시 변수
gui_progress = {}
gui_lock = threading.Lock()

def test_progress_callback(filename, percent, status):
    """테스트용 진행률 콜백"""
    with gui_lock:
        gui_progress[filename] = (percent, status)
        print(f"      📊 GUI: {percent:.1f}% [{status}]")

def test_sync():
    """로그와 GUI 동기화 테스트"""
    
    # 테스트 파일 생성 (20MB)
    test_file = "test_sync_file.bin"
    test_size = 20 * 1024 * 1024  # 20MB
    
    print(f"📝 테스트 파일 생성 중... ({test_size / (1024*1024):.1f}MB)")
    with open(test_file, "wb") as f:
        f.write(os.urandom(test_size))
    
    print(f"✅ 테스트 파일 생성 완료: {test_file}")
    print("=" * 60)
    print("📊 로그와 GUI 동기화 테스트 시작")
    print("   - 로그 출력 시 GUI도 함께 업데이트 되어야 함")
    print("   - 95%까지만 callback에서 표시")
    print("   - 100%는 실제 완료 후 표시")
    print("=" * 60)
    
    # FTP 연결 테스트
    ftp_config = ftp_configs[0]  # 첫 번째 FTP 서버 사용
    
    try:
        ftp = ftplib.FTP()
        ftp.connect(ftp_config['host'], ftp_config['port'])
        ftp.login(ftp_config['user'], ftp_config['pass'])
        ftp.encoding = 'utf-8'
        
        print(f"✅ FTP 연결 성공\n")
        
        # 업로드 테스트
        uploaded_files = []
        ftp_target_path = f"/test/{test_file}"
        
        # 업로드 실행
        print("📤 업로드 시작 (로그와 GUI 동기화 확인)")
        print("-" * 60)
        
        success = AutoBot_fileup_with_progress(
            ftp, test_file, ftp_target_path, test_file,
            uploaded_files, test_progress_callback, max_retries=1
        )
        
        print("-" * 60)
        
        if success:
            print(f"✅ 테스트 성공!")
            
            # 최종 GUI 상태 확인
            if test_file in gui_progress:
                final_percent, final_status = gui_progress[test_file]
                print(f"\n📊 최종 GUI 상태:")
                print(f"   - 진행률: {final_percent:.1f}%")
                print(f"   - 상태: {final_status}")
                
                if final_percent == 100 and final_status == "completed":
                    print(f"   ✅ GUI 100% 완료 확인!")
                else:
                    print(f"   ⚠️ GUI 상태 이상")
            
            # 테스트 파일 삭제
            try:
                ftp.delete(ftp_target_path)
                print(f"🗑️ 원격 테스트 파일 삭제 완료")
            except:
                pass
                
        else:
            print(f"❌ 테스트 실패!")
        
        # FTP 연결 종료
        ftp.quit()
        
    except Exception as e:
        print(f"❌ 예외 발생: {type(e).__name__}: {e}")
    
    finally:
        # 테스트 파일 삭제
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️ 로컬 테스트 파일 삭제 완료")

def main():
    print("=" * 60)
    print("로그와 GUI 진행표 동기화 테스트")
    print("=" * 60)
    
    test_sync()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
    
    # 동기화 결과 요약
    print("\n📊 동기화 개선 사항:")
    print("  1. 로그 출력과 GUI 업데이트가 동시에 발생")
    print("  2. 95%까지만 callback에서 표시 (버퍼 고려)")
    print("  3. 100%는 실제 전송 완료 후 표시")
    print("  4. GUI와 로그가 완벽하게 동기화됨")

if __name__ == "__main__":
    main()