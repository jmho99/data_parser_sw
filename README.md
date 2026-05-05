# Data Parser

## 1. 목적

본 프로젝트는 ROS2 기반 센서 데이터(rosbag/mcap)를 다양한 형식으로 변환하기 위한 **데이터 파서 소프트웨어**입니다.

주요 목표는 다음과 같습니다:

* 센서별 데이터 변환 자동화
* CLI 기반 간편한 사용
* 다양한 출력 포맷 지원 (csv, kml, img, pcd 등)
* 확장 가능한 구조 (카메라, 라이다, GNSS, IMU 등 추가 가능)
* 향후 GUI 연동을 고려한 구조 설계

현재는 GNSS 데이터 변환 기능을 중심으로 개발이 진행 중입니다.

---

## 2. 사용법 (현재: GNSS만 지원)

현재 구현된 기능은 GNSS 데이터 변환입니다.

### 기본 실행

```bash
python3 main.py gnss bag-to-csv <bag_path> -o <output_path> --topics <topic_name>
```

### 예시

```bash
python3 main.py gnss bag-to-csv ~/Downloads/rosbag2_20251113_164845/ -o csv_output --topics /gnss/fix
```

### 주요 옵션

* `gnss` : 센서 타입
* `bag-to-csv` : 변환 기능
* `<bag_path>` : rosbag 또는 mcap 경로
* `-o` : 출력 경로
* `--topics` : 사용할 토픽

---

## 3. 구조

프로젝트는 **센서별 모듈화 + 공용 기능 분리** 구조로 설계되어 있습니다.

```
data_parser/
├── main.py
├── data_parser/
│   ├── cli/
│   ├── core/
│   ├── sensors/
│   └── utils/
```

### 3.1 main.py

* 프로그램의 진입점 (entry point)
* CLI 실행을 담당
* 내부적으로 `cli/main_cli.py`를 호출

---

### 3.2 cli/

```
cli/
└── main_cli.py
```

* 전체 CLI 흐름 제어
* 사용자 입력을 받아 센서별 기능으로 라우팅
* 예: `gnss bag-to-csv` → gnss 모듈 호출

---

### 3.3 core/

```
core/
├── source_type.py
├── source_factory.py
├── schema_loader.py
└── export_format.py
```

공통 핵심 로직 담당

* **source_type.py**

  * 입력 데이터 타입 정의 (rosbag, 향후 mp4 등)

* **source_factory.py**

  * 입력 타입에 맞는 reader 생성

* **schema_loader.py**

  * config / template 기반 필드 구조 로딩

* **export_format.py**

  * 출력 포맷 처리 (csv, kml 등)

---

### 3.4 sensors/

센서별 변환 로직을 분리한 핵심 구조

```
sensors/
├── camera/
├── lidar/
├── gnss/
└── imu/
```

각 센서 폴더는 독립적으로 동작하며, 동일한 인터페이스 구조를 따름

#### GNSS (현재 구현됨)

```
gnss/
├── bag_to_csv.py
```

* `/gnss/fix` 등의 토픽을 읽어 CSV로 변환
* 향후 KML 변환 추가 예정

#### Camera (예정)

* bag → 이미지 추출

#### LiDAR (예정)

* bag → PCD 변환

#### IMU (예정)

* bag → CSV 변환

---

### 3.5 utils/

```
utils/
├── path_utils.py
├── time_utils.py
└── file_utils.py
```

공용 유틸리티 함수 모음

* **path_utils.py**

  * 경로 생성 및 파일명 관리

* **time_utils.py**

  * timestamp 변환

* **file_utils.py**

  * 파일 저장 및 디렉토리 처리

---

## 4. 향후 계획

* GNSS → KML 변환 기능 추가
* LiDAR PCD 변환 구현
* Camera 이미지 추출 기능 구현
* IMU CSV 변환 구현
* config / template 기반 변환 지원
* GUI 인터페이스 추가

---

## 5. 설계 철학

* **센서별 독립 구조**
* **공통 기능 분리**
* **확장성 우선**
* **CLI → GUI 확장 가능 구조**

---

## 6. 현재 상태 요약

| 기능           | 상태     |
| ------------ | ------ |
| GNSS CSV 변환  | ✅ 구현됨  |
| GNSS KML     | ⏳ 예정   |
| Camera       | ⏳ 예정   |
| LiDAR        | ⏳ 예정   |
| IMU          | ⏳ 예정   |
| Config 기반 처리 | ⏳ 설계 중 |

---

필요한 기능이나 구조 변경은 언제든지 확장 가능하도록 설계되어 있습니다.
