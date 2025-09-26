# AutoUp_ftp_utils.py - ProFTPD UTF-8 호환 버전
# FTP 연결 단순화 및 UTF-8 강제 설정

from ftplib import FTP
from AutoUp_env import ftp_configs
import time
import socket

def create_ftp_connection(ftp_name, timeout=30):
    """
    FTP 연결 함수 - UTF-8 강제 설정
    """
    config = ftp_configs[ftp_name]
    print(f"🔌 FTP 연결 시도 중...")
    print(f"   서버: {config['host']}")
    print(f"   포트: {config['port']}")
    print(f"   사용자: {config['user']}")
    
    # 기본 FTP 클래스 사용
    ftp = FTP()
    
    # 디버그 레벨 설정
    ftp.set_debuglevel(1)
    
    # FTP 연결
    ftp.connect(config["host"], int(config["port"]))
    print("   ✓ 서버 연결 성공")
    
    # 로그인
    ftp.login(config["user"], config["password"])
    print("   ✓ 로그인 성공")
    
    # 패시브 모드 설정
    ftp.set_pasv(True)
    print("   ✓ 패시브 모드 설정")
    
    # 인코딩을 UTF-8로 강제 설정 (ProFTPD 1.3.5e with mod_lang)
    ftp.encoding = 'utf-8'
    print(f"   🎯 최종 인코딩: {ftp.encoding}")
    
    # 바이너리 모드 설정
    ftp.voidcmd('TYPE I')
    print("   ✓ 바이너리 모드 설정")
    
    print(f"✅ FTP 연결 성공 ({ftp.host})")
    
    # 연결 테스트
    ftp.voidcmd("NOOP")
    print("   ✓ 연결 테스트 성공")
    
    return ftp

def create_ftp_folder(ftp, path):
    """
    FTP 경로 상의 폴더를 생성
    """
    print(f"📁 FTP 폴더 생성 시작: {path}")
    ftp.cwd("/")
    print("   ✓ 루트 디렉토리로 이동")
    
    try:
        ftp.cwd(path)
        print(f"   ℹ️ 폴더가 이미 존재함: {path}")
    except:
        ftp.mkd(path)
        ftp.cwd(path)
        print(f"   ➕ 새 폴더 생성: {path}")
    
    print(f"✅ 폴더 생성 완료: {path}")
    return path

def reconnect_ftp(ftp, ftp_name, timeout=30):
    """
    FTP 재연결 함수
    """
    try:
        ftp.quit()
    except:
        pass
    
    return create_ftp_connection(ftp_name, timeout)

def check_ftp_connection(ftp):
    """
    FTP 연결 상태 확인
    """
    try:
        ftp.voidcmd("NOOP")
        return True
    except:
        return False
