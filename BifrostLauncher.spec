# 빌드 실행코드
# pyinstaller --clean BifrostLauncher.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 버전 정보 읽기
import re
version = "v0.0.0"
with open('Bifrost.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        version = match.group(1)


a = Analysis(
    ['Bifrost.py'],
    pathex=[],
    binaries=[],
    datas=[], 
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'xml', 'pydoc', 'pdb', 
        'distutils', 'multiprocessing', 'numpy', 'pandas', 'matplotlib'
    ],
    noarchive=False,
    optimize=2, # 최적화 레벨 증가
)

# ▼▼▼▼▼ [용량 줄이기 필터링 유지] ▼▼▼▼▼
remove_list = [
    # 기존 제외 항목
    'opengl32sw.dll', 'qt6network', 'qt6qml', 'qt6quick', 
    'qt6virtualkeyboard', 'd3dcompiler',
    
    # 추가 제외 항목 (공격적)
    'Qt6Pdf', 'Qt6Nfc', 'Qt6Bluetooth', 'Qt6Sensors', 'Qt6SerialPort', 
    'Qt6WebEngine', 'Qt6Multimedia', 'Qt6Positioning', 'Qt6Sql', 
    'Qt6Test', 'Qt6Xml', 'Qt6Svg', # SVG 미사용 시 제외 (사용하면 다시 포함해야 함)
    'Qt6Designer', 'Qt6Help', 'Qt6UiTools', 'Qt63D', 'Qt6Charts',
    'Qt6DataVisualization', 'Qt6RemoteObjects', 'Qt6Scxml', 'Qt6StateMachine',
    'translations' # 다국어 번역 파일 제외
]
a.binaries = [x for x in a.binaries if not any(r in x[0].lower() for r in remove_list)]
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# [변경점 1] EXE는 이제 가볍게 실행 스크립트만 담습니다.
exe = EXE(
    pyz,
    a.scripts,
    [], # binaries와 datas를 여기서 뺍니다.
    exclude_binaries=True, # 중요: 바이너리를 EXE에서 제외합니다.
    name='Bifrost',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\app_icon.ico'],
)

# [변경점 2] COLLECT 블록 추가 (이게 폴더를 만듭니다)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,        # 폴더 내부 파일들도 UPX 압축 시도
    upx_exclude=[],
    name=f'Bifrost_{version}', # dist 폴더 안에 생성될 폴더 이름 (버전 포함)
)