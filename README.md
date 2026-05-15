# Data Parser

## 1. 목적

본 프로젝트는 ROS2 기반 센서 데이터(`rosbag2`, `mcap`, `sqlite3 bag` 등)를 센서별로 읽어 다양한 형식으로 변환하기 위한 **데이터 파서 소프트웨어**입니다.

주요 목표는 다음과 같습니다.

- 센서별 데이터 변환 자동화
- GUI 중심의 쉬운 변환 작업 지원
- CLI 기반 변환 명령 지원
- 카메라, 라이다, GNSS, IMU 데이터 변환 지원
- 다양한 출력 포맷 지원
  - GNSS: CSV, KML
  - Camera: Image, Video
  - LiDAR: PCD
  - IMU: CSV
- 변환 로직과 GUI 분리
- 기능 추가가 쉬운 확장형 구조 구성
- Windows 환경에서도 `pip install` 기반으로 실행 가능한 구조 구성
- PyInstaller를 이용한 단일 실행 파일 배포 지원

현재는 `main.py`를 기준으로 GUI를 바로 실행할 수 있으며, CLI 명령도 함께 사용할 수 있도록 구성되어 있습니다.

---

## 2. 현재 최종 상태

현재 프로젝트는 다음 구조를 기준으로 정리되어 있습니다.

- `main.py` 실행 시 GUI 실행
- 센서별 GUI 페이지 구성 완료
  - GNSS
  - Camera
  - LiDAR
  - IMU
- GUI 입력값과 우측 요약 영역 연동
- 선택 옵션이 많아질 경우 요약 영역 스크롤 처리
- Camera 변환 기능 구성
  - Bag → Image
  - Bag → Video
  - Video → Image
- GNSS 변환 기능 구성
  - Bag → CSV
  - CSV → KML
  - Bag → KML
- LiDAR 변환 기능 구성
  - Bag → PCD
  - ASCII / Binary 저장 방식 선택
  - 저장 필드 선택 구조 반영
- IMU 변환 기능 구성
  - Bag → CSV
  - orientation 포함 저장
- `requirements.txt` 기반 설치 지원
- PyInstaller `--onefile` 기반 exe 배포 가능 구조
- GitHub Release를 통한 exe 배포 가능

---

## 3. 설치 방법

### 3.1 Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Ubuntu / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. 실행 방법

### 4.1 GUI 실행

현재 GUI는 `main.py`에서 바로 실행할 수 있습니다.

```bash
python main.py
```

또는 Linux 환경에서는 다음과 같이 실행할 수 있습니다.

```bash
python3 main.py
```

GUI에서는 센서별 페이지를 선택하여 변환 작업을 수행합니다.

현재 GUI 구성은 다음과 같습니다.

- GNSS 변환
- Camera 변환
- LiDAR 변환
- IMU 변환

---

### 4.2 CLI 실행

CLI는 `main.py` 뒤에 센서 이름과 명령을 입력하여 실행합니다.

```bash
python main.py <sensor> <command> [options]
```

예시:

```bash
python main.py gnss bag-to-csv <bag_path> -o <output_dir> --topics /gnss/fix
```

Linux 환경에서는 다음과 같이 사용할 수 있습니다.

```bash
python3 main.py gnss bag-to-csv <bag_path> -o <output_dir> --topics /gnss/fix
```

---

## 5. 기능

### 5.1 GNSS

GNSS 데이터 변환 기능입니다.

지원 기능:

- Bag → CSV
- CSV → KML
- Bag → KML

예시:

```bash
python main.py gnss bag-to-csv <bag_path> -o <output_dir> --topics /gnss/fix
```

```bash
python main.py gnss csv-to-kml <csv_path> -o <output_name>
```

```bash
python main.py gnss bag-to-kml <bag_path> -o <output_name> --topics /gnss/fix
```

출력 예시:

```text
output/
├── gnss.csv
└── gnss.kml
```

GNSS CSV 저장 데이터 예시:

- timestamp
- latitude
- longitude
- altitude
- status
- covariance

KML 변환 시 GPS 궤적을 Google Earth 또는 지도 프로그램에서 확인할 수 있습니다.

---

### 5.2 Camera

카메라 데이터 변환 기능입니다.

지원 기능:

- Bag → Image
- Bag → Video
- Video → Image

예시:

```bash
python main.py camera bag-to-img <bag_path> -o <output_dir> --topics /camera/image --format png
```

```bash
python main.py camera bag-to-video <bag_path> -o <output_path> --topics /camera/image --format mp4
```

```bash
python main.py camera video-to-img <video_path> -o <output_dir> --format jpg
```

지원 이미지 포맷 예시:

- `png`
- `jpg`
- `jpeg`

지원 비디오 포맷 예시:

- `mp4`
- `avi`
- `webm`

출력 예시:

```text
output/
├── frame_000001.png
├── frame_000002.png
├── frame_000003.png
└── ...
```

또는

```text
output/
└── camera_output.mp4
```

---

### 5.3 LiDAR

라이다 포인트클라우드 변환 기능입니다.

지원 기능:

- Bag → PCD

예시:

```bash
python main.py lidar bag-to-pcd <bag_path> -o <output_dir> --topics /ouster/points --format ascii
```

PCD 저장 방식:

- ASCII
- Binary

GUI에서는 저장 방식과 저장 필드를 선택할 수 있도록 구성되어 있습니다.

저장 필드 예시:

- x
- y
- z
- intensity
- ring
- time
- reflectivity
- ambient
- range

출력 예시:

```text
output/
├── frame_000001_ascii.pcd
├── frame_000002_ascii.pcd
└── ...
```

또는

```text
output/
├── frame_000001_binary.pcd
├── frame_000002_binary.pcd
└── ...
```

---

### 5.4 IMU

IMU 데이터 변환 기능입니다.

지원 기능:

- Bag → CSV

저장 데이터 예시:

- timestamp
- orientation
  - x
  - y
  - z
  - w
- angular_velocity
  - x
  - y
  - z
- linear_acceleration
  - x
  - y
  - z

예시:

```bash
python main.py imu bag-to-csv <bag_path> -o <output_dir> --topics /imu/data
```

출력 예시:

```text
output/
└── imu.csv
```

---

## 6. GUI 구성

GUI는 센서별 페이지로 구성되어 있으며, 각 페이지는 동일한 기본 레이아웃을 사용합니다.

기본 구성:

```text
좌측/상단 입력 영역
 → 변환 모드 선택
 → 입력 파일 또는 폴더 선택
 → 출력 경로 선택
 → topic 입력
 → 저장 포맷 선택
 → 추가 옵션 선택

우측/하단 요약 영역
 → 현재 선택한 변환 조건 표시
 → 출력 설정 표시
 → 추가 옵션 표시
```

현재 GUI 특징:

- 센서별 페이지 구조 통일
- 변환 모드 선택 영역 높이 고정
- 화면 크기에 따라 입력 영역 적응
- 요약 영역은 실제 선택값과 연동
- 옵션이 많아질 경우 요약 영역 스크롤 처리
- theme 파일에서 공통 색상, 폰트, 여백 관리
- GUI는 변환 로직을 직접 갖지 않고 `sensors/` 내부 변환 함수를 호출

---

## 7. 프로젝트 구조

대표 구조는 다음과 같습니다.

```text
data_parser/
├── main.py
├── README.md
├── requirements.txt
├── configs/
│   ├── default.yaml
│   ├── camera.yaml
│   ├── gnss.yaml
│   ├── lidar.yaml
│   └── imu.yaml
│
└── data_parser/
    ├── __init__.py
    │
    ├── cli/
    │   ├── __init__.py
    │   ├── main_cli.py
    │   ├── camera_cli.py
    │   ├── gnss_cli.py
    │   ├── lidar_cli.py
    │   └── imu_cli.py
    │
    ├── gui/
    │   ├── __init__.py
    │   ├── app.py
    │   ├── main_window.py
    │   ├── theme.py
    │   └── pages/
    │       ├── camera_page.py
    │       ├── gnss_page.py
    │       ├── lidar_page.py
    │       └── imu_page.py
    │
    ├── core/
    │   ├── __init__.py
    │   ├── base_source.py
    │   ├── source_factory.py
    │   └── schema_loader.py
    │
    ├── sources/
    │   ├── __init__.py
    │   └── rosbag_source.py
    │
    ├── sensors/
    │   ├── __init__.py
    │   ├── camera/
    │   │   ├── __init__.py
    │   │   ├── bag_to_img.py
    │   │   ├── bag_to_video.py
    │   │   └── video_to_img.py
    │   │
    │   ├── gnss/
    │   │   ├── __init__.py
    │   │   ├── bag_to_csv.py
    │   │   ├── csv_to_kml.py
    │   │   └── bag_to_kml.py
    │   │
    │   ├── lidar/
    │   │   ├── __init__.py
    │   │   └── bag_to_pcd.py
    │   │
    │   └── imu/
    │       ├── __init__.py
    │       └── bag_to_csv.py
    │
    ├── exporters/
    │   ├── __init__.py
    │   ├── csv_exporter.py
    │   ├── kml_exporter.py
    │   ├── image_exporter.py
    │   ├── video_exporter.py
    │   └── pcd_exporter.py
    │
    └── utils/
        ├── __init__.py
        ├── path_utils.py
        ├── time_utils.py
        └── file_utils.py
```

---

## 8. 주요 폴더 설명

### 8.1 main.py

프로젝트의 최상위 실행 진입점입니다.

역할:

- GUI 실행
- CLI 명령 전달
- 실행 모드 분기

실행 예시:

```bash
python main.py
```

```bash
python main.py gnss bag-to-csv ...
```

`main.py`에는 변환 로직이나 GUI 상세 구현을 직접 넣지 않고, 실행 진입점 역할만 두는 것을 원칙으로 합니다.

---

### 8.2 cli/

CLI 명령을 처리하는 폴더입니다.

역할:

- 센서별 CLI 명령 정의
- 입력 인자 파싱
- 변환 함수 호출

구조 예시:

```text
cli/
├── main_cli.py
├── camera_cli.py
├── gnss_cli.py
├── lidar_cli.py
└── imu_cli.py
```

CLI 흐름:

```text
main.py
 → cli/main_cli.py
 → sensor별 cli
 → sensors 내부 변환 함수 호출
```

---

### 8.3 gui/

GUI를 구성하는 폴더입니다.

역할:

- 메인 윈도우 구성
- 센서별 페이지 구성
- 사용자 입력값 수집
- 선택값 요약 표시
- 변환 함수 실행

구조 예시:

```text
gui/
├── app.py
├── main_window.py
├── theme.py
└── pages/
    ├── camera_page.py
    ├── gnss_page.py
    ├── lidar_page.py
    └── imu_page.py
```

GUI 실행:

```bash
python main.py
```

GUI 흐름:

```text
main.py
 → gui/app.py
 → gui/main_window.py
 → gui/pages/*
 → sensors 내부 변환 함수 호출
```

GUI는 변환 로직을 직접 가지지 않고, CLI와 동일한 변환 함수를 사용합니다.

---

### 8.4 core/

공통 핵심 기능을 모아둔 폴더입니다.

역할:

- 입력 source 관리
- source 생성
- config/schema 로딩
- 공통 인터페이스 관리

예시:

```text
core/
├── base_source.py
├── source_factory.py
└── schema_loader.py
```

---

### 8.5 sources/

입력 데이터 source를 다루는 폴더입니다.

현재는 ROS2 bag 계열 데이터를 중심으로 구성합니다.

예시:

```text
sources/
└── rosbag_source.py
```

역할:

- rosbag2 / mcap / sqlite3 bag 경로 처리
- topic 목록 확인
- 메시지 읽기
- 센서별 변환 함수에 데이터 전달

향후 추가 가능한 source 예시:

- video source
- csv source
- image folder source
- pcap source

---

### 8.6 sensors/

센서별 변환 로직을 모아둔 폴더입니다.

구조 예시:

```text
sensors/
├── camera/
├── gnss/
├── lidar/
└── imu/
```

역할:

- 센서별 데이터 파싱
- 센서별 변환 처리
- 저장 포맷에 맞는 데이터 생성

각 센서 폴더는 독립적으로 동작하도록 구성합니다.

---

### 8.7 exporters/

출력 파일 저장 기능을 모아둔 폴더입니다.

예시:

```text
exporters/
├── csv_exporter.py
├── kml_exporter.py
├── image_exporter.py
├── video_exporter.py
└── pcd_exporter.py
```

역할:

- CSV 저장
- KML 저장
- 이미지 저장
- 비디오 저장
- PCD 저장

센서 변환 로직에서 직접 파일 포맷을 모두 처리하지 않도록 분리합니다.

---

### 8.8 configs/

센서별 기본 설정 파일을 저장하는 폴더입니다.

구조:

```text
configs/
├── default.yaml
├── camera.yaml
├── gnss.yaml
├── lidar.yaml
└── imu.yaml
```

역할:

- 기본 topic
- 기본 저장 포맷
- 기본 source type
- 센서별 기본 옵션 관리

예시:

```yaml
source_type: rosbag
default_topic: /gnss/fix
default_format: csv
```

---

### 8.9 utils/

여러 모듈에서 공통으로 사용하는 보조 기능을 모아둔 폴더입니다.

예시:

```text
utils/
├── path_utils.py
├── time_utils.py
└── file_utils.py
```

역할:

- 경로 처리
- 파일명 생성
- 시간 변환
- 확장자 처리
- 출력 폴더 생성
- 중복 파일명 처리

---

## 9. CLI와 GUI 구조

본 프로젝트는 CLI와 GUI가 같은 변환 로직을 사용하도록 구성합니다.

```text
          ┌────────────┐
          │   main.py   │
          └─────┬──────┘
                │
        ┌───────┴────────┐
        │                │
      CLI               GUI
        │                │
        └───────┬────────┘
                │
        sensors/* 변환 로직
                │
          exporters/utils
```

핵심 구조:

- `main.py`는 실행 진입점
- CLI는 명령어 기반 입력 담당
- GUI는 사용자 인터페이스 담당
- 실제 변환은 `sensors/` 내부 함수가 담당
- 파일 저장은 `exporters/`, `utils/`가 보조

---

## 10. Windows exe 배포

PyInstaller를 사용하여 Windows에서 실행 가능한 단일 exe 파일을 만들 수 있습니다.

### 10.1 기본 빌드

```bash
pyinstaller --onefile --windowed --name DataParser main.py
```

빌드 결과는 다음 폴더에 생성됩니다.

```text
dist/
└── DataParser.exe
```

### 10.2 config 파일 포함 빌드

Windows에서는 `--add-data` 구분자로 세미콜론(`;`)을 사용합니다.

```bash
pyinstaller --onefile --windowed --name DataParser --add-data "configs;configs" main.py
```

Linux / Ubuntu에서는 콜론(`:`)을 사용합니다.

```bash
pyinstaller --onefile --windowed --name DataParser --add-data "configs:configs" main.py
```

### 10.3 exe 배포 방식

GitHub Release에 `DataParser.exe`를 업로드하여 배포할 수 있습니다.

예시:

```text
Release tag: v0.1.0
첨부 파일: DataParser.exe
```

사용자는 Python을 설치하지 않아도 exe 파일을 실행할 수 있습니다.

---

## 11. Git 관리 주의사항

다음 파일과 폴더는 Git에 올리지 않는 것을 권장합니다.

```gitignore
# Python cache
__pycache__/
*.py[cod]

# Virtual environment
.venv/
venv/

# PyInstaller
build/
dist/
*.spec

# OS / editor
.DS_Store
.vscode/
.idea/

# Output data
output/
outputs/
results/
```

이미 `__pycache__`가 GitHub에 올라간 경우 다음 명령으로 제거할 수 있습니다.

```bash
git rm -r --cached __pycache__
git commit -m "Remove pycache files"
git push
```

전체 프로젝트에서 `__pycache__`를 제거하려면 다음 명령을 사용할 수 있습니다.

Linux / Ubuntu:

```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Windows PowerShell:

```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

---

## 12. 현재 구현 상태

| 구분 | 기능 | 상태 |
|---|---|---|
| 실행 | `python main.py` GUI 실행 | ✅ |
| 실행 | `python main.py <sensor> ...` CLI 실행 | ✅ |
| 설치 | `requirements.txt` 기반 설치 | ✅ |
| 배포 | PyInstaller `--onefile` exe 빌드 | ✅ |
| GNSS | Bag → CSV | ✅ |
| GNSS | CSV → KML | ✅ |
| GNSS | Bag → KML | ✅ |
| Camera | Bag → Image | ✅ |
| Camera | Bag → Video | ✅ |
| Camera | Video → Image | ✅ |
| LiDAR | Bag → PCD | ✅ |
| LiDAR | PCD ASCII 저장 | ✅ |
| LiDAR | PCD Binary 저장 | ✅ |
| LiDAR | 저장 필드 선택 구조 | ✅ |
| IMU | Bag → CSV | ✅ |
| IMU | orientation 저장 | ✅ |
| GUI | GNSS Page | ✅ |
| GUI | Camera Page | ✅ |
| GUI | LiDAR Page | ✅ |
| GUI | IMU Page | ✅ |
| GUI | 선택값 요약 표시 | ✅ |
| GUI | 요약 영역 스크롤 처리 | ✅ |
| GUI | 공통 theme 적용 | ✅ |

---

## 13. 설계 원칙

### 13.1 로직과 UI 분리

GUI에는 변환 로직을 직접 넣지 않습니다.

```text
GUI 버튼 클릭
 → 입력값 수집
 → sensors 변환 함수 호출
 → 결과 출력
```

이 구조를 유지하면 CLI와 GUI 결과가 동일하게 유지됩니다.

---

### 13.2 센서별 독립 구조

카메라, 라이다, GNSS, IMU 기능은 서로 독립된 폴더에 둡니다.

장점:

- 기능 수정 범위가 명확함
- 센서 추가가 쉬움
- 특정 센서 오류가 다른 센서에 영향을 덜 줌

---

### 13.3 source와 sensor 분리

입력 데이터는 `sources/`에서 읽고, 센서별 처리는 `sensors/`에서 수행합니다.

예시:

```text
rosbag_source.py
 → 메시지 읽기
 → sensors/gnss 변환
 → csv/kml 저장
```

향후 rosbag 외 입력이 추가되어도 source만 추가하면 됩니다.

예시:

- video source
- csv source
- image folder source
- pcap source

---

### 13.4 GUI와 CLI는 같은 함수를 사용한다

같은 기능을 GUI용, CLI용으로 따로 만들지 않습니다.

좋은 구조:

```text
CLI  → convert_bag_to_csv()
GUI  → convert_bag_to_csv()
```

나쁜 구조:

```text
CLI용 convert 함수
GUI용 convert 함수
```

---

### 13.5 main.py에는 실행 분기만 둔다

`main.py`에 변환 로직이나 GUI 클래스를 직접 넣지 않습니다.

좋은 구조:

```text
main.py
 → gui.app.main()
```

```text
main.py
 → cli.main_cli.main()
```

나쁜 구조:

```text
main.py 안에 GUI 클래스 직접 작성
main.py 안에 변환 함수 직접 작성
```

---

### 13.6 출력 경로와 파일명 처리 분리

출력 경로 생성, 확장자 처리, 파일명 자동 생성은 가능하면 `utils/`로 분리합니다.

예시:

```text
output_dir 생성
확장자 자동 추가
중복 파일명 처리
```

---

### 13.7 센서별 기본값은 config에서 관리한다

topic 이름, 기본 저장 포맷, source type 등은 config 파일에서 관리합니다.

예시:

```yaml
source_type: rosbag
default_topic: /gnss/fix
default_format: csv
```

---

## 14. 개발 시 주의사항

### 14.1 순환 import 방지

센서별 변환 함수는 서로 직접 import하지 않는 것을 권장합니다.

예를 들어 `bag_to_kml.py`에서 `csv_to_kml.py` 기능이 필요할 경우, 공통 함수만 분리해서 import하는 방식이 좋습니다.

좋은 구조:

```text
gnss/
├── bag_to_csv.py
├── csv_to_kml.py
├── bag_to_kml.py
└── common.py
```

나쁜 구조:

```text
csv_to_kml.py가 bag_to_kml.py를 import
bag_to_kml.py가 csv_to_kml.py를 import
```

---

### 14.2 GUI는 표시와 입력만 담당

GUI 파일에서는 다음 작업만 담당합니다.

- 입력값 수집
- 버튼 이벤트 처리
- 요약 표시
- 변환 함수 호출
- 성공/실패 메시지 표시

실제 변환은 `sensors/` 내부에서 처리합니다.

---

### 14.3 센서 기능 추가 순서

새 기능을 추가할 때는 다음 순서로 확장합니다.

```text
1. sensors/<sensor>/ 에 변환 함수 추가
2. cli/<sensor>_cli.py 에 CLI 명령 추가
3. gui/pages/<sensor>_page.py 에 GUI 입력 추가
4. 필요한 경우 configs/<sensor>.yaml 수정
5. README.md 사용법 업데이트
```

---

## 15. 향후 개선 예정

추후 추가하면 좋은 기능은 다음과 같습니다.

- topic 자동 탐색
- rosbag 내부 topic 목록 GUI 표시
- 변환 진행률 표시
- 변환 로그 저장
- 에러 로그 파일 저장
- 다중 topic 일괄 변환
- 출력 파일명 자동 규칙 설정
- GUI 설정값 저장/불러오기
- 최근 사용 경로 저장
- 변환 완료 후 결과 폴더 열기
- exe 아이콘 적용
- GitHub Release 자동 빌드
- Ubuntu AppImage 또는 deb 패키징
- Windows installer 제작

---

## 16. 요약

Data Parser는 ROS2 기반 센서 데이터를 센서별로 변환하기 위한 CLI + GUI 통합 도구입니다.

현재 구조의 핵심은 다음과 같습니다.

```text
main.py
 → GUI 또는 CLI 실행
 → 센서별 변환 함수 호출
 → 출력 포맷별 저장
```

현재 지원 센서는 다음과 같습니다.

- GNSS
- Camera
- LiDAR
- IMU

현재 지원 출력 포맷은 다음과 같습니다.

- CSV
- KML
- Image
- Video
- PCD

이 구조를 유지하면 기능이 추가되어도 전체 구조를 크게 바꾸지 않고 확장할 수 있습니다.