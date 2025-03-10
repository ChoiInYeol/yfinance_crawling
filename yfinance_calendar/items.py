# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YFinanceCalendarItem(scrapy.Item):
    """Yahoo Finance 캘린더 데이터를 저장하는 아이템
    
    Attributes:
        calendar_type (str): 캘린더 타입 (earnings, economic, ipo, splits)
        date (str): 데이터 날짜 (YYYY-MM-DD 형식)
        title (str): 주요 제목 (보통 '심볼 - 회사명' 또는 '이벤트명' 형식)
        subtitle (str): 부제목 (이벤트 설명, 비율 등)
        additional_data (dict): 각 캘린더 타입별 상세 데이터를 저장하는 딕셔너리
        metadata (dict): 크롤링 메타데이터 (소스, 크롤링 시간 등)
    
    additional_data 구조:
    1. earnings:
       - symbol (str): 종목 심볼
       - company (str): 회사명
       - event_name (str): 이벤트명
       - call_time (str): 실적발표 시간
       - eps_estimate (str): EPS 추정치
       - reported_eps (str): 실제 EPS
       - surprise (str): 서프라이즈 비율 (%)
       
    2. economic:
       - event (str): 이벤트명
       - country (str): 국가
       - event_time (str): 이벤트 시간
       - event_for (str): 해당 기간
       - actual (str): 실제값
       - market_expectation (str): 시장 예상치
       - prior (str): 이전 수치
       - revised_from (str): 수정 전 수치
       
    3. ipo:
       - symbol (str): 종목 심볼
       - company (str): 회사명
       - exchange (str): 거래소
       - ipo_date (str): IPO 날짜
       - price_range (str): 가격 범위
       - price (str): 가격
       - currency (str): 통화
       - shares (str): 주식 수
       - actions (str): 액션 (Expected, Priced 등)
       
    4. splits:
       - symbol (str): 종목 심볼
       - company (str): 회사명
       - payable_on (str): 지급일
       - optionable (str): 옵션 가능 여부
       - ratio (str): 분할 비율
    """
    calendar_type = scrapy.Field()  # str: 캘린더 타입 (earnings, economic, ipo, splits)
    date = scrapy.Field()           # str: 데이터 날짜 (YYYY-MM-DD 형식)
    title = scrapy.Field()          # str: 주요 제목 표시용
    subtitle = scrapy.Field()       # str: 부제목 표시용
    additional_data = scrapy.Field() # dict: 각 캘린더 타입별 추가 데이터를 저장할 딕셔너리
    metadata = scrapy.Field()       # dict: 크롤링 메타데이터
    
    # 호환성을 위한 속성
    @property
    def symbol(self):
        """str: 종목 심볼 (additional_data에서 추출)"""
        if self.get('additional_data') and 'symbol' in self['additional_data']:
            return self['additional_data']['symbol']
        return ''
    
    @property
    def company(self):
        """str: 회사명 (additional_data에서 추출)"""
        if self.get('additional_data') and 'company' in self['additional_data']:
            return self['additional_data']['company']
        return ''
    
    @property
    def event_name(self):
        """str: 이벤트명 (additional_data에서 추출)"""
        if self.get('additional_data') and 'event_name' in self['additional_data']:
            return self['additional_data']['event_name']
        elif self.get('additional_data') and 'event' in self['additional_data']:
            return self['additional_data']['event']
        return ''
    
    @property
    def time(self):
        """str: 이벤트 시간 (additional_data에서 추출)"""
        if self.get('additional_data') and 'call_time' in self['additional_data']:
            return self['additional_data']['call_time']
        elif self.get('additional_data') and 'event_time' in self['additional_data']:
            return self['additional_data']['event_time']
        return ''
