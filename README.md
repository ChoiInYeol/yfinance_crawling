# Yahoo Finance 이벤트 기반 주가 분석 시스템 기술 보고서

## 개요

본 보고서는 Yahoo Finance의 기업 실적 발표 및 경제 지표 데이터를 자동으로 수집하고, 이를 기반으로 이벤트 전후의 주가 변동을 분석하는 시스템의 구현 내용을 상세히 기술합니다.

## I. 시스템 구성 및 데이터 수집 프로세스

### 1. 데이터 소스

본 시스템은 Yahoo Finance Calendar (https://finance.yahoo.com/calendar) 페이지의 다음 섹션들을 주요 데이터 소스로 활용합니다:

1) 실적 발표 (Earnings): https://finance.yahoo.com/calendar/earnings
2) 경제 지표 (Economic Events): https://finance.yahoo.com/calendar/economic
3) 기업공개 (IPO): https://finance.yahoo.com/calendar/ipo
4) 주식 분할 (Stock Splits): https://finance.yahoo.com/calendar/splits

### 2. 크롤링 시스템 아키텍처

크롤링 시스템은 Scrapy 프레임워크를 기반으로 구현되었으며, 다음과 같은 컴포넌트로 구성됩니다:

```
crawler_yf_event/
├── spiders/
│   └── yf_calendar_spider.py  # 크롤링 로직
├── items.py                   # 데이터 모델
├── pipelines.py              # 데이터 처리
├── settings.py               # 환경 설정
└── run_crawler.py            # 실행 스크립트
```

### 3. 데이터 수집 프로세스

#### 3.1 크롤러 실행 방법

크롤러는 다음과 같은 명령어로 실행할 수 있습니다:

```bash
# 기본 실행 (현재 날짜 기준 전후 7일)
python run_crawler.py

# 날짜 범위 지정 실행
python run_crawler.py --start-date 2024-03-01 --end-date 2024-03-31

# 특정 이벤트 타입만 수집
python run_crawler.py --events earnings,economic

# 수집 기간 조정
python run_crawler.py --days 30
```

#### 3.2 데이터 추출 메커니즘

Yahoo Finance의 캘린더 페이지에서 데이터를 추출하는 과정은 다음과 같습니다:

1) **페이지 구조 분석**
   ```python
   # 테이블 데이터 위치 XPath
   table_xpath = '//*[@id="cal-res-table"]'
   
   # 실적 발표 데이터 예시
   headers_xpath = './/thead/tr/th/text()'
   rows_xpath = './/tbody/tr'
   ```

2) **페이지네이션 처리**
   - 기본 페이지 크기: 100개 항목
   - URL 파라미터: offset={n}, size=100
   - 최대 수집 제한: earnings의 경우 1000개

3) **데이터 정제**
   - HTML 이스케이프 처리
   - 숫자 데이터 타입 변환
   - 날짜 형식 표준화

### 4. 수집 데이터 구조

#### 4.1 실적 발표 데이터 (earnings)
```json
{
    "event_type": "earnings",
    "date": "2024-03-10",
    "symbol": "AAPL",
    "company": "Apple Inc.",
    "eps_estimate": "1.50",
    "reported_eps": "1.55",
    "surprise": "3.33",
    "call_time": "After Market Close"
}
```

#### 4.2 경제 지표 데이터 (economic)
```json
{
    "event_type": "economic",
    "date": "2024-03-10",
    "event": "GDP Growth Rate",
    "country": "United States",
    "actual": "2.1",
    "estimate": "2.0",
    "prior": "2.0"
}
```

## II. 주가 데이터 수집 및 분석

### 1. 주가 데이터 수집

수집된 이벤트 데이터를 기반으로 관련 기업들의 주가 데이터를 yfinance API를 통해 자동으로 수집합니다:

```python
import yfinance as yf

# 주가 데이터 다운로드
ticker = yf.Ticker("AAPL")
hist = ticker.history(
    start="2024-01-01",
    end="2024-03-10",
    interval="1d"
)
```

### 2. 이벤트 영향 분석

#### 2.1 분석 지표
- 이벤트 전후 3개월 주가 변동
- 일일 수익률 변동성
- 거래량 변화
- 실적 서프라이즈와 주가 반응 상관관계

#### 2.2 시각화 결과
분석 결과는 HTML 형식의 인터랙티브 리포트로 생성됩니다:
- 개별 기업 이벤트 영향 차트
- 시가총액 기준 상위 기업 비교 분석
- 서프라이즈 효과 분석 차트

## III. 시스템 한계 및 향후 개선 방안

### 1. 현재 한계점

1) **데이터 수집 제약**
   - Yahoo Finance의 요청 제한
   - 실시간 데이터 지연 (15-20분)
   - 과거 데이터의 제한적 접근

2) **분석 범위 제한**
   - 시가총액 상위 기업 중심 분석
   - 제한된 이벤트 유형

### 2. 향후 개선 방안

1) **데이터 소스 확장**
   - 추가 금융 데이터 제공자 통합
   - 소셜 미디어 센티먼트 분석 추가

2) **분석 고도화**
   - 머신러닝 모델 도입
   - 실시간 알림 시스템 구축
   - 포트폴리오 최적화 기능 추가

3) **시스템 안정성 강화**
   - 분산 크롤링 시스템 도입
   - 데이터 검증 프로세스 강화
   - 백업 및 복구 시스템 구축

## IV. 설치 및 실행 요구사항

### 1. 시스템 요구사항
- Python >= 3.11
- 메모리: 4GB 이상
- 저장공간: 1GB 이상

### 2. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 설정
```bash
# 프로젝트 루트 디렉토리에서
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

## V. 라이선스 및 법적 고지

본 시스템은 MIT 라이선스 하에 배포되며, Yahoo Finance의 이용 약관을 준수합니다. 수집된 데이터의 상업적 사용 시 관련 법규를 확인하시기 바랍니다.

---
작성자: [시스템 개발팀]
작성일: 2024년 3월 10일
버전: 1.0.0 