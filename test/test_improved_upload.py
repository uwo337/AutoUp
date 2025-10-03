#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스크립트 - 개선된 업로드 로직 테스트
"""

import os
import sys
import time
import ftplib
from AutoUp_upload_util import AutoBot_fileup_with_progress, UploadStuckError, UploadIncompleteError
from AutoUp_env import ftp_configs

def test_upload():
    """개선된 업로드 로직 테스트"""
    
    # 테스트 파일 생성 (10MB)
    test_file = "test_upload_file.bin"
    test_size = 10 * 1024 * 1024  # 10MB
    
    print(f"📝 테스트 파일 생성 중... ({test_size / (1024*1024):.1f}MB)")
    with open(test_file, "wb") as f:
        f.write(os.urandom(test_size))
    
    print(f"✅ 테스트 파일 생성 완료: {test_file}")
    
    # FTP 연결 테스트
    ftp_config = ftp_configs[0]  # 첫 번째 FTP 서버 사용
    print(f"\n📡 FTP 연결 시도: {ftp_config['host']}:{ftp_config['port']}")
    
    try:
        ftp = ftplib.FTP()
        ftp.connect(ftp_config['host'], ftp_config['port'])
        ftp.login(ftp_config['user'], ftp_config['pass'])
        ftp.encoding = 'utf-8'
        
        print(f"✅ FTP 연결 성공")
        
        # 업로드 테스트
        print(f"\n📤 업로드 테스트 시작...")
        
        # 진행률 콜백
        def progress_callback(filename, percent, status):
            if status == "uploading":
                print(f"   📊 진행률: {percent:.1f}%", end="\r")
            elif status == "completed":
                print(f"\n   ✅ 업로드 완료!")
            elif status == "failed":
                print(f"\n   ❌ 업로드 실패!")
        
        uploaded_files = []
        ftp_target_path = f"/test/{test_file}"
        
        # 업로드 실행
        success = AutoBot_fileup_with_progress(
            ftp, test_file, ftp_target_path, test_file,
            uploaded_files, progress_callback, max_retries=2
        )
        
        if success:
            print(f"✅ 테스트 성공! 업로드된 파일: {uploaded_files}")
            
            # 업로드된 파일 크기 확인
            remote_size = ftp.size(ftp_target_path)
            print(f"📊 로컬 파일: {test_size:,} bytes")
            print(f"📊 원격 파일: {remote_size:,} bytes")
            
            if remote_size == test_size:
                print(f"✅ 파일 크기 일치!")
            else:
                print(f"⚠️ 파일 크기 불일치!")
            
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
        
    except UploadStuckError as e:
        print(f"❌ 업로드 멈춤 감지: {e}")
    except UploadIncompleteError as e:
        print(f"❌ 불완전한 업로드: {e}")
    except Exception as e:
        print(f"❌ 예외 발생: {type(e).__name__}: {e}")
    
    finally:
        # 테스트 파일 삭제
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️ 로컬 테스트 파일 삭제 완료")

if __name__ == "__main__":
    print("=" * 60)
    print("개선된 업로드 로직 테스트")
    print("=" * 60)
    
    test_upload()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)