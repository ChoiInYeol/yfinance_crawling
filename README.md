# Yahoo Finance Calendar Crawler

Yahoo Finance의 캘린더 데이터를 수집하는 Scrapy 기반 크롤러입니다.

## 기능

다음 4가지 캘린더 타입의 데이터를 수집합니다:

1. **Earnings (실적 발표)**
   - 기업 실적 발표 일정
   - EPS 추정치, 실제 EPS, 서프라이즈 등

2. **Economic (경제 지표)**
   - 각국의 경제 지표 발표
   - 실제값, 예상치, 이전값 등

3. **IPO (기업공개)**
   - 신규 상장 일정
   - 거래소, 공모가 범위, 주식수 등

4. **Stock Splits (주식 분할)**
   - 주식 분할 일정
   - 분할 비율, 지급일 등

## 설치 방법

1. Python 3.11 이상이 필요합니다.

2. Poetry를 사용하여 의존성을 설치합니다:
```bash
poetry install
```

## 사용 방법

### 1. 기본 실행 (Scrapy 직접 실행)
```bash
poetry run scrapy crawl yahoo_calendar
```
- 기본적으로 오늘부터 7일간의 데이터를 수집합니다.

### 2. 데이터 처리 스크립트 실행
```bash
# 기본 실행 (현재 시각 기준으로 파일명 자동 생성)
poetry run python process_calendar_data.py
# 결과: calendar_data_20240310_153021_earnings.json
#       calendar_data_20240310_153021_economic.json
#       calendar_data_20240310_153021_ipo.json
#       calendar_data_20240310_153021_splits.json

# 날짜 범위 지정
poetry run python process_calendar_data.py --start-date 2024-03-10 --end-date 2024-03-17

# 출력 파일명 접두사 지정
poetry run python process_calendar_data.py --output my_calendar_data
# 결과: my_calendar_data_earnings.json
#       my_calendar_data_economic.json
#       my_calendar_data_ipo.json
#       my_calendar_data_splits.json
```

### 스크립트 옵션 설명
- `--start-date`: 시작일 (YYYY-MM-DD 형식)
- `--end-date`: 종료일 (YYYY-MM-DD 형식)
- `--output`: 출력 파일명 접두사 (미지정시 현재 시각 기반으로 자동 생성)

## 데이터 처리

### JSON에서 DataFrame으로 변환
```python
from yfinance_calendar.utils import json_to_dataframe

# JSON 파일 읽기
dataframes = json_to_dataframe('calendar_data.json')

# 캘린더 타입별 DataFrame 접근
earnings_df = dataframes['earnings']
economic_df = dataframes['economic']
ipo_df = dataframes['ipo']
splits_df = dataframes['splits']
```

### DataFrame 구조

각 캘린더 타입별 DataFrame은 다음과 같은 컬럼 구조를 가집니다:

1. **Earnings (실적 발표)**
```python
columns = [
    '날짜',         # datetime64[ns]
    '종목코드',     # str
    '기업명',       # str
    '회계분기',     # str (Q1-Q4)
    '회계연도',     # str
    '실적발표시간',  # str (Before Market Open, After Market Close, ...)
    'EPS예상',     # float64
    'EPS실제',     # float64
    '서프라이즈'    # float64
]
```

2. **Economic (경제 지표)**
```python
columns = [
    '날짜',       # datetime64[ns]
    '지표명',     # str
    '국가',       # str
    '대상기간',   # str
    '실제값',     # float64
    '예상치',     # float64
    '이전값',     # float64
    '수정전값'    # float64
]
```

3. **IPO (기업공개)**
```python
columns = [
    '날짜',        # datetime64[ns]
    '종목코드',    # str
    '기업명',      # str
    '거래소',      # str
    '공모가범위',  # str
    '확정공모가',  # str
    '공모주식수'   # str
]
```

4. **Stock Splits (주식 분할)**
```python
columns = [
    '날짜',          # datetime64[ns]
    '종목코드',      # str
    '기업명',        # str
    '지급일',        # datetime64[ns]
    '옵션가능여부',  # str
    '분할비율'       # str
]
```

### 데이터 처리 예시

```python
from yfinance_calendar.utils import json_to_dataframe

# JSON 파일 읽기
dataframes = json_to_dataframe('calendar_data.json')

# 실적 발표 데이터 처리
earnings_df = dataframes['earnings']
# EPS 서프라이즈가 10% 이상인 기업 찾기
surprise_companies = earnings_df[earnings_df['서프라이즈'] >= 10]

# 경제 지표 데이터 처리
economic_df = dataframes['economic']
# 특정 국가의 경제 지표 필터링
us_indicators = economic_df[economic_df['국가'] == 'United States']

# IPO 데이터 처리
ipo_df = dataframes['ipo']
# 특정 거래소의 IPO 목록
nasdaq_ipos = ipo_df[ipo_df['거래소'] == 'NASDAQ']

# 주식 분할 데이터 처리
splits_df = dataframes['splits']
# 다음 달에 예정된 주식 분할
next_month_splits = splits_df[splits_df['지급일'].dt.month == (datetime.now().month + 1)]
```

## 데이터 구조

수집된 데이터는 다음과 같은 구조를 가집니다:

```json
{
    "calendar_type": "earnings|economic|ipo|splits",
    "date": "YYYY-MM-DD",
    "symbol": "티커심볼",
    "company": "회사명",
    "event_name": "이벤트명",
    "time": "이벤트 시간",
    "additional_data": {
        // 캘린더 타입별 추가 데이터
    }
}
```

### 캘린더 타입별 additional_data 구조

1. Earnings
```json
{
    "fiscal_quarter": "Q1/Q2/Q3/Q4",
    "fiscal_year": "회계연도",
    "event_title": "원본 이벤트명",
    "call_time": "실적발표 시간",  // Before Market Open, After Market Close, During Market Trading, Time Not Supplied
    "eps_estimate": "예상 EPS",
    "reported_eps": "실제 EPS",
    "surprise": "서프라이즈(%)",
    "market_cap": "시가총액",  // 향후 추가 예정
    "revenue_estimate": "매출 추정치",  // 향후 추가 예정
    "call_status": "실적발표 상태"  // Scheduled, Completed, Cancelled
}
```

2. Economic
```json
{
    "event": "이벤트명",
    "country": "국가",
    "for": "대상 기간",
    "actual": "실제값",
    "market_expectation": "시장 예상치",
    "prior": "이전값",
    "revised_from": "수정전 값"
}
```

3. IPO
```json
{
    "exchange": "거래소",
    "date": "상장일",
    "price_range": "공모가 범위",
    "price": "확정 공모가",
    "shares": "공모 주식수"
}
```

4. Stock Splits
```json
{
    "payable_date": "지급일",
    "optionable": "옵션 가능 여부",
    "ratio": "분할 비율"
}
```

## 주의사항

1. 과도한 요청을 방지하기 위해 기본적으로 1초의 딜레이가 설정되어 있습니다.
2. 404 에러가 발생하는 페이지는 자동으로 건너뜁니다.
3. 데이터 처리 중 오류가 발생해도 크롤링이 중단되지 않고 계속 진행됩니다.

## 의존성

- Python >= 3.11
- scrapy >= 2.12.0
- twisted >= 24.11.0
- service-identity >= 24.1.0

## 라이선스

MIT License 