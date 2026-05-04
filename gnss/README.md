## GNSS 데이터 .kml로 변환

  구글 지도에서 궤적 확인을 위한 데이터 변환
  
### 1. /fix 토픽을 .csv 파일로 변환

  rosbag_to_csv.py
  
  python3 rosbag_to_csv.py [ros2bag direct] -o [output name] --topics [topic name]
  
### 2. .csv파일을 .kml 파일로 변환

  fix_csv_to_kml.py
  
  python3 fix_csv_to_kml.py [csv direct] [output name]
  
### 3. 구글 맵에 .kml 업로드

  1. google my map 접속 (https://www.google.com/maps/d/u/0/)
  2. 새 지도 만들기
  3. 레이어 추가
  4. 가져오기
  5. 저장된 .kml 파일 선택

### 샘플 데이터
  
  https://www.microsoft.com/en-us/download/details.aspx?id=52367
  https://zenodo.org/records/18155248
