# Data Parser

## 1. 목적

본 프로젝트는 ROS2 기반 센서 데이터(rosbag/mcap)를 다양한 형식으로 변환하기 위한 **데이터 파서 소프트웨어**입니다.

주요 목표:

* 센서별 데이터 변환 자동화
* CLI + GUI 동시 지원
* 다양한 출력 포맷 지원 (csv, kml, img, pcd 등)
* 확장 가능한 구조 (카메라, 라이다, GNSS, IMU 등)
* 변환 로직과 UI 분리

현재는 GNSS 데이터 변환과 GUI 실행 구조까지 구성된 상태입니다.

---

## 2. 사용법 (현재: GNSS)

### 2.1 CLI 사용

```bash
python3 main.py gnss bag-to-csv <bag_path> -o <output_path> --topics <topic_name>
```

#### 예시

```bash
python3 main.py gnss bag-to-csv ~/Downloads/rosbag2_20251113_164845/ -o csv_output --topics /gnss/fix
```

---

### 2.2 GUI 사용

현재 GUI는 `main.py`를 통해 실행되지 않으며, 모듈 실행 방식으로 구동합니다.

```bash
python3 -m data_parser.gui.app
```

#### GUI 기능

* bag 경로 선택
* topic 입력
* 출력 경로 설정
* GNSS CSV 변환 실행

#### 특징

* CLI 변환 로직을 그대로 재사용
* GUI는 입력/실행 인터페이스 역할만 수행
* 변환 로직은 sensors 내부 코드 사용

---

## 3. 구조

```text
data_parser/
├── main.py
├── data_parser/
│   ├── cli/
│   ├── gui/
│   ├── core/
│   ├── sensors/
│   └── utils/
```

---

### 3.1 main.py

* CLI 전용 진입점
* GUI 실행은 포함하지 않음

```bash
python3 main.py gnss ...
```

---

### 3.2 cli/

```text
cli/
└── main_cli.py
```

* CLI 명령 처리
* 센서 기능 호출 및 라우팅

---

### 3.3 gui/

```text
gui/
├── app.py
├── main_window.py
└── widgets/
```

GUI 구성

#### 실행 방식

```bash
python3 -m data_parser.gui.app
```

#### 역할

* 사용자 입력 UI 제공
* 내부적으로 sensors 변환 함수 호출

#### 구조 흐름

```text
GUI 입력
 → 파라미터 생성
 → sensors/*/convert() 호출
```

#### 특징

* 비즈니스 로직 없음
* CLI와 동일한 결과 보장
* 추후 기능 확장 시 UI만 추가하면 됨

---

### 3.4 core/

```text
core/
├── source_type.py
├── source_factory.py
├── schema_loader.py
└── export_format.py
```

공통 핵심 로직

* 입력 타입 관리 (rosbag 등)
* reader 생성
* config/template 처리
* 출력 형식 처리

---

### 3.5 sensors/

```text
sensors/
├── camera/
├── lidar/
├── gnss/
└── imu/
```

센서별 변환 모듈

#### GNSS (현재 구현됨)

```text
gnss/
└── bag_to_csv.py
```

* GNSS topic → CSV 변환

#### 향후 확장

* GNSS → KML
* Camera → IMG
* LiDAR → PCD
* IMU → CSV

---

### 3.6 utils/

```text
utils/
├── path_utils.py
├── time_utils.py
└── file_utils.py
```

공용 유틸

* 경로 처리
* 시간 변환
* 파일 저장

---

## 4. CLI vs GUI 구조

```text
[CLI]                [GUI]
  │                    │
  └──────┬─────────────┘
         ↓
   sensors/* 변환 로직
```

핵심:

* CLI와 GUI는 입력 방식만 다름
* 실제 변환 로직은 완전히 동일
* 유지보수 및 확장 용이

---

## 5. 향후 계획

* GNSS → KML 추가
* LiDAR PCD 변환 구현
* Camera 이미지 추출
* IMU CSV 변환
* config / template 기반 변환
* GUI 기능 확장 (탭 분리, 자동 topic 탐색 등)

---

## 6. 현재 상태

| 기능       | 상태           |
| -------- | ------------ |
| GNSS CSV | ✅            |
| GUI 실행   | ✅ (모듈 실행 방식) |
| GNSS KML | ⏳            |
| Camera   | ⏳            |
| LiDAR    | ⏳            |
| IMU      | ⏳            |

---

## 7. 설계 철학

* 로직(UI) 분리
* 센서별 독립 구조
* 확장성 우선
* CLI → GUI 자연 확장

---

현재 구조를 유지하면
👉 변환 기능 추가 시 sensors만 수정
👉 GUI/CLI는 그대로 재사용 가능

이라는 장점이 있습니다.
