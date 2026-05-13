# Data Parser

## 1. 목적

본 프로젝트는 ROS2 기반 센서 데이터(`rosbag2`, `mcap` 등)를 센서별로 읽어 다양한 형식으로 변환하기 위한 **데이터 파서 소프트웨어**입니다.

주요 목표는 다음과 같습니다.

- 센서별 데이터 변환 자동화
- CLI와 GUI 동시 지원
- 카메라, 라이다, GNSS, IMU 데이터 변환 지원
- 다양한 출력 포맷 지원
  - GNSS: CSV, KML
  - Camera: IMG, VIDEO
  - LiDAR: PCD
  - IMU: CSV
- 변환 로직과 UI 분리
- 기능 추가가 쉬운 확장형 구조 구성

현재는 `main.py`를 기준으로 CLI와 GUI를 모두 실행할 수 있도록 구성되어 있습니다.

---

## 2. 실행 방법

## 2.1 GUI 실행

GUI는 `main.py`에서 바로 실행할 수 있습니다.

```bash
python3 main.py gui
```

GUI에서는 센서별 탭을 통해 변환 작업을 수행합니다.

현재 GUI 구성은 다음과 같습니다.

- GNSS 변환
- Camera 변환
- LiDAR 변환
- IMU 변환

---

## 2.2 CLI 실행

CLI는 기존처럼 `main.py` 뒤에 센서 이름과 명령을 입력하여 실행합니다.

```bash
python3 main.py <sensor> <command> [options]
```

예시:

```bash
python3 main.py gnss bag-to-csv ~/Downloads/rosbag2_20251113_164845 -o ./output --topics /gnss/fix
```

---

## 3. 기능

## 3.1 GNSS

GNSS 데이터 변환 기능입니다.

지원 기능:

- Bag → CSV
- CSV → KML
- Bag → KML

예시:

```bash
python3 main.py gnss bag-to-csv <bag_path> -o <output_dir> --topics /gnss/fix
```

```bash
python3 main.py gnss csv-to-kml <csv_path> -o <output_name>
```

```bash
python3 main.py gnss bag-to-kml <bag_path> -o <output_name> --topics /gnss/fix
```

출력 예시:

```text
output/
├── gnss.csv
└── gnss.kml
```

---

## 3.2 Camera

카메라 데이터 변환 기능입니다.

지원 기능:

- Bag → Image
- Bag → Video
- Video → Image

예시:

```bash
python3 main.py camera bag-to-img <bag_path> -o <output_dir> --topics /camera/image --format png
```

```bash
python3 main.py camera bag-to-video <bag_path> -o <output_path> --topics /camera/image --format mp4
```

```bash
python3 main.py camera video-to-img <video_path> -o <output_dir> --format jpg
```

지원 포맷 예시:

- 이미지: `png`, `jpg`
- 비디오: `mp4`, `avi`, `webm`

---

## 3.3 LiDAR

라이다 포인트클라우드 변환 기능입니다.

지원 기능:

- Bag → PCD

예시:

```bash
python3 main.py lidar bag-to-pcd <bag_path> -o <output_dir> --topics /ouster/points --format ascii
```

PCD 저장 방식:

- ASCII
- Binary

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

## 3.4 IMU

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
python3 main.py imu bag-to-csv <bag_path> -o <output_dir> --topics /imu/data
```

출력 예시:

```text
output/
└── imu.csv
```

---

## 4. 프로젝트 구조

```text
data_parser/
├── main.py
├── configs/
│   ├── default.yaml
│   ├── camera.yaml
│   ├── gnss.yaml
│   ├── lidar.yaml
│   └── imu.yaml
│
└── data_parser/
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
    │   ├── gnss/
    │   ├── lidar/
    │   └── imu/
    │
    ├── exporters/
    │   ├── __init__.py
    │   └── pcd_exporter.py
    │
    └── utils/
        ├── __init__.py
        ├── path_utils.py
        ├── time_utils.py
        └── file_utils.py
```

---

## 5. 주요 폴더 설명

## 5.1 main.py

프로젝트의 최상위 실행 진입점입니다.

역할:

- `python3 main.py gui` 입력 시 GUI 실행
- 그 외 명령은 CLI로 전달

실행 예시:

```bash
python3 main.py gui
```

```bash
python3 main.py gnss bag-to-csv ...
```

---

## 5.2 cli/

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

## 5.3 gui/

GUI를 구성하는 폴더입니다.

역할:

- 메인 윈도우 구성
- 센서별 페이지 구성
- 사용자 입력값 수집
- 변환 함수 실행

구조 예시:

```text
gui/
├── app.py
├── main_window.py
└── pages/
    ├── camera_page.py
    ├── gnss_page.py
    ├── lidar_page.py
    └── imu_page.py
```

GUI 실행:

```bash
python3 main.py gui
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

## 5.4 core/

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

## 5.5 sources/

입력 데이터 source를 다루는 폴더입니다.

현재는 ROS2 bag source를 중심으로 구성합니다.

예시:

```text
sources/
└── rosbag_source.py
```

역할:

- rosbag2/mcap 파일 열기
- topic 목록 확인
- 메시지 읽기
- 센서별 변환 함수에 데이터 전달

---

## 5.6 sensors/

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

## 5.7 exporters/

출력 파일 저장 기능을 모아둔 폴더입니다.

예시:

```text
exporters/
└── pcd_exporter.py
```

역할:

- PCD 저장
- CSV 저장
- KML 저장
- 이미지/비디오 저장 보조 기능

센서 변환 로직에서 직접 파일 포맷을 모두 처리하지 않도록 분리합니다.

---

## 5.8 configs/

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

---

## 5.9 utils/

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

---

## 6. CLI와 GUI 구조

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

## 7. 현재 구현 상태

| 구분 | 기능 | 상태 |
|---|---|---|
| 실행 | `python3 main.py gui` | ✅ |
| 실행 | `python3 main.py <sensor> ...` | ✅ |
| GNSS | Bag → CSV | ✅ |
| GNSS | CSV → KML | ✅ |
| GNSS | Bag → KML | ✅ |
| Camera | Bag → Image | ✅ |
| Camera | Bag → Video | ✅ |
| Camera | Video → Image | ✅ |
| LiDAR | Bag → PCD | ✅ |
| LiDAR | PCD ASCII 저장 | ✅ |
| LiDAR | PCD Binary 저장 | ✅ / 함수 확장 가능 구조 |
| IMU | Bag → CSV | ✅ |
| GUI | GNSS Page | ✅ |
| GUI | Camera Page | ✅ |
| GUI | LiDAR Page | ✅ |
| GUI | IMU Page | ✅ |

---

## 8. 설계 원칙

## 8.1 로직과 UI 분리

GUI에는 변환 로직을 직접 넣지 않습니다.

```text
GUI 버튼 클릭
 → 입력값 수집
 → sensors 변환 함수 호출
 → 결과 출력
```

이 구조를 유지하면 CLI와 GUI 결과가 동일하게 유지됩니다.

---

## 8.2 센서별 독립 구조

카메라, 라이다, GNSS, IMU 기능은 서로 독립된 폴더에 둡니다.

장점:

- 기능 수정 범위가 명확함
- 센서 추가가 쉬움
- 특정 센서 오류가 다른 센서에 영향을 덜 줌

---

## 8.3 source와 sensor 분리

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

## 8.4 확장 가능한 명령 구조

새 기능을 추가할 때는 다음 순서로 확장합니다.

```text
1. sensors/<sensor>/ 에 변환 함수 추가
2. cli/<sensor>_cli.py 에 CLI 명령 추가
3. gui/pages/<sensor>_page.py 에 GUI 입력 추가
4. 필요한 경우 configs/<sensor>.yaml 수정
```

---

## 9. 개발 시 주의사항

## 9.1 main.py에는 실행 분기만 둔다

`main.py`에 변환 로직이나 GUI 코드를 직접 넣지 않습니다.

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

## 9.2 GUI와 CLI는 같은 함수를 사용한다

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

## 9.3 출력 경로와 파일명 처리 분리

출력 경로 생성, 확장자 처리, 파일명 자동 생성은 가능하면 `utils/`로 분리합니다.

예시:

```text
output_dir 생성
확장자 자동 추가
중복 파일명 처리
```

---

## 9.4 센서별 기본값은 config에서 관리한다

topic 이름, 기본 저장 포맷, source type 등은 config 파일에서 관리합니다.

예시:

```yaml
source_type: rosbag
default_topic: /gnss/fix
default_format: csv
```

---

## 10. 향후 개선 예정

추후 추가하면 좋은 기능은 다음과 같습니다.

- topic 자동 탐색
- rosbag 내부 topic 목록 GUI 표시
- 변환 진행률 표시
- 변환 로그 저장
- 에러 로그 파일 저장
- 다중 topic 일괄 변환
- 출력 파일명 자동 규칙 설정
- GUI 설정값 저장/불러오기
- 실행 파일 패키징
  - Ubuntu: AppImage 또는 deb
  - Windows: exe

---

## 11. 요약

Data Parser는 ROS2 기반 센서 데이터를 센서별로 변환하기 위한 CLI + GUI 통합 도구입니다.

현재 구조의 핵심은 다음과 같습니다.

```text
main.py
 → CLI 또는 GUI 실행
 → 센서별 변환 함수 호출
 → 출력 포맷별 저장
```

이 구조를 유지하면 기능이 추가되어도 전체 구조를 크게 바꾸지 않고 확장할 수 있습니다.