import os
import configparser
import sys
import pkgutil

# ✅ ini 파일을 PyInstaller 리소스로부터 직접 읽기
if getattr(sys, 'frozen', False):
    data = pkgutil.get_data(__name__, "AutoUp_env.ini")
    config_string = data.decode("utf-8")
else:
    with open("AutoUp_env.ini", "r", encoding="utf-8") as f:
        config_string = f.read()

# ✅ ConfigParser는 문자열에서도 읽을 수 있다
_config = configparser.ConfigParser()
from io import StringIO
_config.read_file(StringIO(config_string))

# ✅ 이후 기존 코드와 동일
selected_ftp_name = "FTP1"
BBS_URL_1 = _config.get("BBS", "bbsUrl_1").strip()
BBS_URL_2 = _config.get("BBS", "bbsUrl_2").strip()

WEBDOWN_DIR = _config.get("env", "webDefaultDown").strip()
TORRENT_DIR = _config.get("env", "downfolder").strip()
NETWORK_DELAY = _config.getfloat("env", "netwrok_delay")

LOGIN_USER = _config["FTP_LOGIN"]["user"]
LOGIN_PW   = _config["FTP_LOGIN"]["password"]

FTP_SERVER_NAMES = ["FTP1", "FTP2", "FTP3"]
ftp_configs = {}
for name in FTP_SERVER_NAMES:
    section = _config[name]
    ftp_configs[name] = {
        "host": section["host"],
        "port": section.getint("port"),
        "user": LOGIN_USER,
        "password": LOGIN_PW
    }
