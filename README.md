# Bifrost (바이프로스트)

**Bifrost**는 Python과 PySide6로 제작된 프리미엄 스타일의 데스크탑 런처입니다. 사용자가 자주 사용하는 애플리케이션, 폴더, 웹사이트를 그룹별로 효율적으로 관리하고 빠르게 실행할 수 있도록 돕습니다. 어두운 테마(Dark Mode)를 기반으로 한 직관적이고 세련된 UI를 제공합니다.

## ✨ 주요 기능 (Key Features)

*   **그룹 기반 관리 (Group Tabs)**: 앱과 링크를 탭 형태의 그룹으로 나누어 깔끔하게 정리할 수 있습니다.
*   **드래그 앤 드롭 (Drag & Drop)**: 파일, 실행 파일(.exe), 바로가기(.lnk), 또는 URL을 드래그하여 손쉽게 추가할 수 있습니다.
*   **아이콘 자동 추출 및 관리**:
    *   실행 파일 및 바로가기의 아이콘을 자동으로 추출합니다.
    *   웹사이트 URL 추가 시 파비콘(Favicon)을 자동으로 가져옵니다.
    *   사용되지 않는 아이콘을 자동으로 정리하는 스마트한 관리 기능을 포함합니다.
*   **단축키 지원 (Shortcuts)**:
    *   각 그룹(탭) 이동을 위한 숫자 단축키 (예: `1`, `2`, `3`...).
    *   개별 앱 실행을 위한 사용자 지정 키보드 단축키 매핑.
*   **반응형 레이아웃 (Flow Layout)**: 창 크기에 따라 아이콘 배치가 자연스럽게 조정됩니다.
*   **항상 위 (Always on Top)**: 설정에서 런처를 항상 최상위에 두도록 고정할 수 있습니다.
*   **프리미엄 UI**: 가독성이 뛰어난 다크 테마와 세련된 호버 효과, 애니메이션이 적용되어 있습니다.

## 🛠️ 기술 스택 (Tech Stack)

*   **Language**: Python 3.10+
*   **GUI Framework**: PySide6 (Qt for Python)
*   **Image Processing**: Pillow (PIL)
*   **Build Tool**: PyInstaller

## ⚙️ 설치 및 실행 (Installation & Usage)

### 전제 조건
시스템에 [Python](https://www.python.org/)이 설치되어 있어야 합니다.

### 의존성 설치
프로젝트 실행에 필요한 라이브러리를 설치합니다.
```bash
pip install PySide6 Pillow
```

### 실행
`Bifrost.py` 파일을 직접 실행하여 런처를 시작합니다.
```bash
python Bifrost.py
```

### 빌드 (Executable)
PyInstaller를 사용하여 단일 실행 파일(.exe)로 빌드할 수 있습니다. 포함된 `BifrostLauncher.spec` 파일을 사용합니다.
```bash
pyinstaller BifrostLauncher.spec
```

## 📝 설정 (Configuration)

설정은 `config.json` 파일에 저장되며, 앱 내에서 변경 시 자동으로 업데이트됩니다.

*   `apps`: 등록된 앱/링크의 정보 (이름, 경로, 아이콘, 단축키 등) 리스트
*   `settings`:
    *   `always_on_top`: 항상 위 기능 활성화 여부
    *   `group_order`: 탭 순서
    *   `group_shortcuts`: 탭 전환 단축키
    *   `window_geometry`: 창의 위치 및 크기 정보

## 📂 프로젝트 구조

```
Bifrost/
├── Bifrost.py           # 메인 애플리케이션 소스 코드
├── BifrostLauncher.spec # PyInstaller 빌드 스펙 파일
├── config.json          # 사용자 설정 및 앱 데이터
├── README.md            # 프로젝트 설명서
├── icons/               # 추출된 아이콘 저장소
└── build/ & dist/       # 빌드 결과물 디렉토리
```

---
**AntiGravity Portfolio** - *Efficiency meets Aesthetics*
