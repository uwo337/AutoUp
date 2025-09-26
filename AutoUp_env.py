# AutoUp_env_standalone.py - 단독 실행용 (ini 파일 불필요)
import os

# 전역 변수
selected_ftp_name = "FTP1"

# BBS URL 설정
BBS_URL_1 = "http://www.boadisk.com/club/basic/bbs.php?clubid=hiddenfile&bbscode=173426470368222"
BBS_URL_2 = "http://www.boadisk.com/club/basic/bbs.php?clubid=world&bbscode=172933244218524"

# 디렉토리 설정 - 사용자 폴더 자동 감지
# 사용자의 Downloads 폴더 자동 찾기
WEBDOWN_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# D:\down 폴더가 있으면 사용, 없으면 사용자 Downloads 사용
if os.path.exists(r"D:\down"):
    TORRENT_DIR = r"D:\down"
else:
    TORRENT_DIR = WEBDOWN_DIR

NETWORK_DELAY = 3.0

# FTP 로그인 정보
LOGIN_USER = "test1"
LOGIN_PW = "Hi9144629!@"

# FTP 서버 설정
FTP_SERVER_NAMES = ["FTP1", "FTP2", "FTP3"]
ftp_configs = {
    "FTP1": {
        "host": "38.95.100.90",
        "port": 2002,
        "user": LOGIN_USER,
        "password": LOGIN_PW
    },
    "FTP2": {
        "host": "38.95.100.159",
        "port": 2002,  # ProFTPD 1.3.5e with mod_lang (UTF-8 지원)
        "user": LOGIN_USER,
        "password": LOGIN_PW
    },
    "FTP3": {
        "host": "38.126.53.20",
        "port": 2002,
        "user": LOGIN_USER,
        "password": LOGIN_PW
    }
}
