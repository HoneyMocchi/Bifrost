import re
import subprocess
import sys
import os

def get_version():
    """Bifrost.py에서 VERSION 상수를 추출합니다."""
    try:
        with open('Bifrost.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'VERSION\s*=\s*"v(\d+)\.(\d+)\.(\d+)"', content)
            if match:
                return match.groups() # ('0', '4', '5')
    except Exception as e:
        print(f"Bifrost.py 읽기 실패: {e}")
    return None

def update_version_info(major, minor, patch):
    """version_info.txt 파일의 버전을 업데이트합니다."""
    try:
        with open('version_info.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 튜플 업데이트: filevers=(0, 4, 4, 0)
        ver_tuple = f"({major}, {minor}, {patch}, 0)"
        content = re.sub(r'filevers=\(\d+, \d+, \d+, \d+\)', f'filevers={ver_tuple}', content)
        content = re.sub(r'prodvers=\(\d+, \d+, \d+, \d+\)', f'prodvers={ver_tuple}', content)
        
        # 2. 문자열 업데이트: u'0.4.4.0'
        ver_str = f"u'{major}.{minor}.{patch}.0'"
        content = re.sub(r"StringStruct\(u'FileVersion', u'[\d\.]+'\)", f"StringStruct(u'FileVersion', {ver_str})", content)
        content = re.sub(r"StringStruct\(u'ProductVersion', u'[\d\.]+'\)", f"StringStruct(u'ProductVersion', {ver_str})", content)
        
        with open('version_info.txt', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"version_info.txt 업데이트 완료: {major}.{minor}.{patch}.0")
        return True
    except Exception as e:
        print(f"version_info.txt 업데이트 실패: {e}")
        return False

def build():
    print("--- Bifrost 빌드 스크립트 ---")
    
    # 1. 버전 정보 추출
    v = get_version()
    if not v:
        print("Bifrost.py에서 VERSION 상수를 찾을 수 없습니다. (형식: VERSION = \"v0.0.0\")")
        sys.exit(1)
    
    print(f"감지된 버전: v{v[0]}.{v[1]}.{v[2]}")
    
    # 2. 버전 정보 파일 동기화
    if not update_version_info(*v):
        sys.exit(1)
        
    # 3. PyInstaller 실행 (기존 빌드 캐시 정리 포함)
    print("PyInstaller 실행 중...")
    cmd = ['pyinstaller', '--clean', 'BifrostLauncher.spec']
    
    try:
        # build 폴더 권한 문제 등으로 실패할 수 있으나, subprocess가 에러 코드를 반환하면 감지됨
        subprocess.check_call(cmd, shell=True)
        print("빌드 성공! (dist 폴더 확인)")
    except subprocess.CalledProcessError:
        print("PyInstaller 빌드 실패.")

if __name__ == '__main__':
    build()
