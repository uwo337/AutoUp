import json
import io
import os
import re

def sanitize_filename(filename):
    """
    Windows 금지문자 제거: \\ / : * ? " < > | '
    """
    forbidden_pattern = re.compile(r'[\\/:*?"<>|\']')
    safe_name = forbidden_pattern.sub('', filename)
    return safe_name.strip()

def build_info_json(entry):
    """
    🔹 성공한 업로드 결과를 info.json 형식으로 생성 (경로명 제거 → 파일명만, 기존 금지 기호 제거)
    """
    images = [ sanitize_filename(os.path.basename(path)) for path in entry.get("images", []) ]
    files = [ sanitize_filename(os.path.basename(path)) for path in entry.get("files", []) ]

    return {
        "target_url": entry["target_url"],
        "prefix": entry.get("prefix", ""),
        "title": entry["title"],
        "content": entry.get("content", []),
        "images": images,
        "files": files
    }

def save_info_json(info_data, ftp, remote_path): 
    """
    🔹 info.json을 UTF-8로 저장 (FTP 업로드)
    """
    json_data = json.dumps(info_data, ensure_ascii=False, indent=2)
    bio = io.BytesIO(json_data.encode("utf-8"))
    print(f"📌 현재 FTP 작업 디렉토리: {ftp.pwd()} → 저장 대상: {remote_path}")
    ftp.storbinary(f"STOR {remote_path}", bio)

