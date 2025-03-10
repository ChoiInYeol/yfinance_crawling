import scrapy
from datetime import datetime, timedelta
from urllib.parse import urlencode
from ..items import YFinanceCalendarItem


class YahooFinanceCalendarSpider(scrapy.Spider):
    """Yahoo Finance 캘린더 데이터를 수집하는 스파이더
    
    이 스파이더는 Yahoo Finance의 다음 4가지 캘린더 데이터를 수집합니다:
    - Earnings (실적 발표)
    - Economic (경제 지표)
    - IPO (기업공개)
    - Splits (주식 분할)
    
    각 캘린더 타입별로 지정된 날짜 범위의 데이터를 수집하며,
    페이지네이션을 처리하여 모든 결과를 가져옵니다.
    """
    
    name = 'yahoo_calendar'
    allowed_domains = ['finance.yahoo.com']
    
    # 수집할 캘린더 타입들
    calendar_types = ['earnings', 'economic', 'ipo', 'splits']
    # 한 페이지당 결과 수 (야후 파이낸스 최대값으로 복원)
    results_per_page = 100

    # Scrapy 설정 - 원래 값으로 복원
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # 요청 간 3초 딜레이
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 딜레이에 랜덤성 추가
        'CONCURRENT_REQUESTS': 2,  # 동시 요청 수
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # 도메인당 동시 요청 수
        'COOKIES_ENABLED': False,  # 쿠키 비비활성화
        'RETRY_TIMES': 3,  # 재시도 횟수
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],  # 재시도할 HTTP 코드
        'DOWNLOAD_TIMEOUT': 30,  # 타임아웃
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'yahoo_calendar_spider.log',
        'LOG_STDOUT': True
    }

    # 기본 헤더 설정
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Ch-Ua': '"Chromium";v="123", "Not:A-Brand";v="8"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }
    
    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        """
        스파이더 초기화
        
        Args:
            start_date (str, optional): 시작 날짜 (YYYY-MM-DD). Defaults to None.
            end_date (str, optional): 종료 날짜 (YYYY-MM-DD). Defaults to None.
        """
        super(YahooFinanceCalendarSpider, self).__init__(*args, **kwargs)
        
        # 시작일 기본값: 현재 날짜 (오늘)
        if start_date:
            self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            self.start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        # 종료일 기본값: 시작일 + 7일
        if end_date:
            self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            self.end_date = self.start_date + timedelta(days=7)
            
        # 날짜 범위 재조정 - 오류 수정: 시작 날짜는 정확히 지정된 날짜부터
        self.date_range = []
        current_date = self.start_date
        while current_date <= self.end_date:
            self.date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
            
        self.logger.info(f"수집 날짜 범위: {self.date_range[0]} ~ {self.date_range[-1]} ({len(self.date_range)}일)")
        self.total_items = 0
        # 캘린더 타입별 수집 현황 추적
        self.collection_status = {}
    
    def start_requests(self):
        """
        각 캘린더 타입별, 날짜별 요청 생성
        """
        for calendar_type in self.calendar_types:
            for date in self.date_range:
                url = f'https://finance.yahoo.com/calendar/{calendar_type}'
                
                # 날짜별로 요청 생성 ('day' 파라미터 사용)
                params = {
                    'day': date,
                    'size': self.results_per_page,
                    'offset': 0
                }
                
                # URL에 파라미터 추가
                full_url = f"{url}?{urlencode(params)}"
                
                self.logger.info(f"요청 생성: {calendar_type.capitalize()} 데이터 - {date}")
                
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse,
                    errback=self.errback_httpbin,
                    headers=self.custom_headers,
                    meta={
                        'calendar_type': calendar_type,
                        'date': date,
                        'offset': 0,
                        'current_date': date
                    }
                )
    
    def errback_httpbin(self, failure):
        """
        요청 실패 처리 콜백
        """
        request = failure.request
        calendar_type = request.meta.get('calendar_type', '')
        date = request.meta.get('date', '')
        self.logger.error(f"요청 실패: {calendar_type} - {date}, URL: {request.url}, 오류: {repr(failure)}")
    
    def parse(self, response):
        """
        응답 파싱 및 데이터 추출
        
        캘린더 타입별로 다른 데이터 구조를 처리하고
        페이지네이션 처리
        """
        calendar_type = response.meta['calendar_type']
        current_date = response.meta['current_date']
        offset = response.meta['offset']
        
        # 캘린더 타입별 수집 현황 초기화
        if calendar_type not in self.collection_status:
            self.collection_status[calendar_type] = {
                'total': 0,
                'collected': 0,
                'date': current_date
            }
        
        # 전체 결과 수 확인 (정확한 XPath 사용)
        total_results_text = response.xpath('/html/body/div[2]/main/section/section/section/article/section/section[1]/div[1]/div/div/p/text()').get('')
        self.logger.debug(f"전체 결과 수 텍스트: {total_results_text}")
        
        # 테이블 선택 (정확한 XPath 사용)
        table = response.xpath('/html/body/div[2]/main/section/section/section/article/section/section[1]/div[2]/table')
        if not table:
            self.logger.warning(f"테이블이 없음: {calendar_type} - {current_date}")
            # 디버깅을 위한 추가 정보 로깅
            self.logger.debug(f"페이지 내용: {response.text[:1000]}")  # 처음 1000자만 로깅
            return
            
        # 테이블 행 선택 - 정확한 XPath 사용 및 누락 데이터 추적
        expected_rows = list(range(1, 101))  # 1부터 100까지의 행 번호
        found_rows = []  # 실제로 찾은 행 번호
        valid_rows = []  # 유효한 데이터가 있는 행
        
        for row_num in expected_rows:
            # 특정 번호의 행을 직접 선택
            row_xpath = f'/html/body/div[2]/main/section/section/section/article/section/section[1]/div[2]/table/tbody/tr[{row_num}]'
            row = response.xpath(row_xpath)
            
            if row:
                found_rows.append(row_num)
                if row.xpath('.//td'):  # td가 있는 행만 유효한 데이터로 취급
                    valid_rows.append(row)
        
        # 누락된 행 번호 확인
        missing_rows = set(expected_rows) - set(found_rows)
        if missing_rows:
            self.logger.warning(f"누락된 행 번호들: {sorted(list(missing_rows))}")
            self.logger.debug(f"총 예상 행 수: {len(expected_rows)}, 실제 찾은 행 수: {len(found_rows)}, 유효한 행 수: {len(valid_rows)}")
        
        actual_row_count = len(valid_rows)
        
        if actual_row_count == 0:
            self.logger.warning(f"유효한 데이터 행이 없음: {calendar_type} - {current_date}")
            return
        
        # 페이지네이션 버튼 확인 (정확한 XPath 사용)
        next_button = response.xpath('/html/body/div[2]/main/section/section/section/article/section/section[1]/div[3]/div[3]/button[3]')
        has_next = bool(next_button)
        if has_next:
            self.logger.debug("다음 페이지 버튼 발견")
            # 버튼의 disabled 속성 확인
            is_disabled = next_button.xpath('@disabled').get() == 'true'
            button_text = next_button.xpath('text()').get('')
            has_next = not is_disabled and button_text == 'Next'
            self.logger.debug(f"다음 페이지 버튼 상태: {'활성화' if has_next else '비활성화'}, 텍스트: {button_text}")
        
        # 총 결과 수 추출
        total_results = 0
        if total_results_text:
            try:
                # "XXX results" 형식에서 숫자만 추출
                total_results = int(''.join(filter(str.isdigit, total_results_text)))
                self.collection_status[calendar_type]['total'] = total_results
                self.logger.debug(f"전체 결과 수: {total_results}")
            except (ValueError, IndexError) as e:
                self.logger.error(f"전체 결과 수 파싱 오류: {e}, 텍스트: {total_results_text}")
                total_results = actual_row_count
        
        # 현재 진행 상황 업데이트 및 로깅
        current_collected = offset + actual_row_count
        self.collection_status[calendar_type]['collected'] = current_collected
        
        # 진행률 계산 (0으로 나누기 방지)
        progress_percentage = (current_collected / total_results * 100) if total_results > 0 else 0
        
        progress_msg = (
            f"진행 상황: {calendar_type.upper()} - "
            f"{current_collected}/{total_results} 항목 수집 "
            f"({progress_percentage:.1f}%), 현재 페이지 행 수: {actual_row_count}"
        )
        self.logger.info(progress_msg)
        
        # 테이블 행 처리
        for row in valid_rows:
            try:
                # 아이템 생성
                item = YFinanceCalendarItem()
                item['calendar_type'] = calendar_type
                item['date'] = current_date
                
                # 셀 데이터 추출 (XPath 사용)
                cells = row.xpath('.//td')
                
                if not cells:  # 셀이 없는 경우 로깅 후 스킵
                    self.logger.debug(f"셀이 없는 행 발견: {row.get()}")
                    continue

                if calendar_type == 'earnings':
                    # Symbol (str): 종목 심볼
                    symbol_link = row.xpath('.//td[1]//a/text()').get('').strip()
                    symbol = symbol_link if symbol_link else row.xpath('.//td[1]//text()').get('').strip()
                    
                    # Company (str): 회사명
                    company = row.xpath('.//td[2]//text()').get('').strip()
                    
                    # Event Name (str): 이벤트명
                    event_name = row.xpath('.//td[3]//text()').get('').strip()
                    
                    # Earnings Call Time (str): 실적발표 시간
                    call_time = row.xpath('.//td[4]//text()').get('').strip()
                    
                    # EPS Estimate (str): EPS 추정치
                    eps_estimate = row.xpath('.//td[5]//text()').get('').strip()
                    
                    # Reported EPS (str): 실제 EPS
                    reported_eps = row.xpath('.//td[6]//text()').get('').strip()
                    
                    # Surprise (%) (str): 서프라이즈 비율
                    surprise = row.xpath('.//td[7]//text()').get('').strip()
                    
                    # 데이터 검증 (Symbol과 Company 필드가 비어있는지 확인)
                    if not symbol and not company:
                        self.logger.debug(f"Symbol과 Company 모두 누락: {row.get()}")
                        continue
                    
                    # 데이터 구조 통일
                    item['title'] = f"{symbol} - {company}" if symbol and company else (symbol or company)
                    item['subtitle'] = event_name if event_name and event_name != '-' else call_time
                    item['additional_data'] = {
                        'symbol': symbol or None,              # str: 종목 심볼
                        'company': company or None,            # str: 회사명
                        'event_name': event_name or None,      # str: 이벤트명
                        'call_time': call_time or None,        # str: 실적발표 시간
                        'eps_estimate': eps_estimate or None,  # str: EPS 추정치
                        'reported_eps': reported_eps or None,  # str: 실제 EPS
                        'surprise': surprise or None           # str: 서프라이즈 비율 (%)
                    }
                    
                    self.logger.debug(f"Earnings 데이터: Symbol={symbol}, Company={company}, "
                                    f"Event={event_name}, Time={call_time}, "
                                    f"EPS Est={eps_estimate}, EPS Rep={reported_eps}, "
                                    f"Surprise={surprise}")
                
                elif calendar_type == 'economic':
                    # Event (str): 이벤트명
                    event = cells[0].css('::text').get('').strip() if len(cells) > 0 else ''
                    # Country (str): 국가
                    country = cells[1].css('::text').get('').strip() if len(cells) > 1 else ''
                    # Event Time (str): 이벤트 시간
                    event_time = cells[2].css('::text').get('').strip() if len(cells) > 2 else ''
                    # For (str): 해당 기간
                    event_for = cells[3].css('::text').get('').strip() if len(cells) > 3 else ''
                    # Actual (str): 실제값
                    actual = cells[4].css('::text').get('').strip() if len(cells) > 4 else ''
                    # Market Expectation (str): 시장 예상치
                    market_exp = cells[5].css('::text').get('').strip() if len(cells) > 5 else ''
                    # Prior to This (str): 이전 수치
                    prior = cells[6].css('::text').get('').strip() if len(cells) > 6 else ''
                    # Revised from (str): 수정 전 수치
                    revised = cells[7].css('::text').get('').strip() if len(cells) > 7 else ''
                    
                    # 데이터 구조 통일
                    item['title'] = f"{event}"
                    item['subtitle'] = f"{country} | {event_for}" if country and event_for else (country or event_for or "Economic Event")
                    item['additional_data'] = {
                        'event': event,                      # str: 이벤트명
                        'country': country,                  # str: 국가 코드
                        'event_time': event_time,            # str: 이벤트 시간
                        'event_for': event_for,              # str: 해당 기간
                        'actual': actual,                    # str: 실제값
                        'market_expectation': market_exp,    # str: 시장 예상치
                        'prior': prior,                      # str: 이전 수치
                        'revised_from': revised              # str: 수정 전 수치
                    }
                    
                    self.logger.debug(f"Economic 데이터: Event={event}, Country={country}, "
                                    f"Time={event_time}, For={event_for}, "
                                    f"Actual={actual}, Exp={market_exp}, Prior={prior}, "
                                    f"Revised={revised}")
                
                elif calendar_type == 'ipo':
                    # Symbol (str): 종목 심볼 (첫 번째 셀의 a 태그 텍스트)
                    symbol_link = cells[0].css('a.loud-link::text').get('').strip()
                    symbol = symbol_link if symbol_link else cells[0].css('div ::text').get('').strip()
                    
                    # Company (str): 회사명
                    company = cells[1].css('::text').get('').strip() if len(cells) > 1 else ''
                    # Exchange (str): 거래소
                    exchange = cells[2].css('::text').get('').strip() if len(cells) > 2 else ''
                    # Date (str): IPO 날짜
                    ipo_date = cells[3].css('::text').get('').strip() if len(cells) > 3 else ''
                    # Price Range (str): 가격 범위
                    price_range = cells[4].css('::text').get('').strip() if len(cells) > 4 else ''
                    # Price (str): 가격
                    price = cells[5].css('::text').get('').strip() if len(cells) > 5 else ''
                    # Currency (str): 통화
                    currency = cells[6].css('::text').get('').strip() if len(cells) > 6 else ''
                    # Shares (str): 주식 수
                    shares = cells[7].css('::text').get('').strip() if len(cells) > 7 else ''
                    # Actions (str): 액션
                    actions = cells[8].css('::text').get('').strip() if len(cells) > 8 else ''
                    
                    # 데이터 검증 (Symbol과 Company 필드가 비어있는지 확인)
                    if not symbol or not company:
                        self.logger.warning(f"Symbol 또는 Company 누락: Symbol={symbol}, Company={company}")
                        # 추가 디버깅을 위한 HTML 출력
                        self.logger.debug(f"원본 HTML: {row.get()}")
                    
                    # 데이터 구조 통일
                    item['title'] = f"{symbol} - {company}"
                    item['subtitle'] = f"IPO on {exchange}" if exchange else "IPO"
                    item['additional_data'] = {
                        'symbol': symbol,              # str: 종목 심볼
                        'company': company,            # str: 회사명
                        'exchange': exchange,          # str: 거래소
                        'ipo_date': ipo_date,          # str: IPO 날짜
                        'price_range': price_range,    # str: 가격 범위
                        'price': price,                # str: 가격
                        'currency': currency,          # str: 통화
                        'shares': shares,              # str: 주식 수
                        'actions': actions             # str: 액션 (Expected, Priced 등)
                    }
                    
                    self.logger.debug(f"IPO 데이터: Symbol={symbol}, Company={company}, "
                                    f"Exchange={exchange}, Date={ipo_date}, "
                                    f"Price Range={price_range}, Price={price}, Currency={currency}, "
                                    f"Shares={shares}, Actions={actions}")
                
                elif calendar_type == 'splits':
                    # Symbol (str): 종목 심볼 (첫 번째 셀의 a 태그 텍스트)
                    symbol_link = cells[0].css('a.loud-link::text').get('').strip()
                    symbol = symbol_link if symbol_link else cells[0].css('div ::text').get('').strip()
                    
                    # Company (str): 회사명
                    company = cells[1].css('::text').get('').strip() if len(cells) > 1 else ''
                    # Payable On (str): 지급일
                    payable_on = cells[2].css('::text').get('').strip() if len(cells) > 2 else ''
                    # Optionable (str): 옵션 가능 여부
                    optionable = cells[3].css('::text').get('').strip() if len(cells) > 3 else ''
                    # Ratio (str): 분할 비율
                    ratio = cells[4].css('::text').get('').strip() if len(cells) > 4 else ''
                    
                    # 데이터 검증 (Symbol과 Company 필드가 비어있는지 확인)
                    if not symbol or not company:
                        self.logger.warning(f"Symbol 또는 Company 누락: Symbol={symbol}, Company={company}")
                        # 추가 디버깅을 위한 HTML 출력
                        self.logger.debug(f"원본 HTML: {row.get()}")
                    
                    # 데이터 구조 통일
                    item['title'] = f"{symbol} - {company}"
                    item['subtitle'] = f"Split Ratio: {ratio}" if ratio else "Stock Split"
                    item['additional_data'] = {
                        'symbol': symbol,              # str: 종목 심볼
                        'company': company,            # str: 회사명
                        'payable_on': payable_on,      # str: 지급일
                        'optionable': optionable,      # str: 옵션 가능 여부
                        'ratio': ratio                 # str: 분할 비율
                    }
                    
                    self.logger.debug(f"Split 데이터: Symbol={symbol}, Company={company}, "
                                    f"Payable On={payable_on}, Optionable={optionable}, "
                                    f"Ratio={ratio}")
                
                # 항목이 유효한지 확인
                if calendar_type == 'earnings':
                    # earnings는 symbol이 필수
                    if not item['additional_data'].get('symbol'):
                        self.logger.warning(f"유효하지 않은 Earnings 항목 (Symbol 누락): {item}")
                        continue
                elif calendar_type == 'economic':
                    # economic은 event가 필수
                    if not item['additional_data'].get('event'):
                        self.logger.warning(f"유효하지 않은 Economic 항목 (Event 누락): {item}")
                        continue
                elif calendar_type == 'ipo':
                    # ipo는 symbol이 필수
                    if not item['additional_data'].get('symbol'):
                        self.logger.warning(f"유효하지 않은 IPO 항목 (Symbol 누락): {item}")
                        continue
                elif calendar_type == 'splits':
                    # splits는 symbol이 필수
                    if not item['additional_data'].get('symbol'):
                        self.logger.warning(f"유효하지 않은 Split 항목 (Symbol 누락): {item}")
                        continue

                # 메타데이터 추가
                item['metadata'] = {
                    'source': 'yahoo_finance',
                    'crawled_at': datetime.now().isoformat(),
                    'calendar_type': calendar_type,
                    'date': current_date
                }

                # 항목이 유효할 경우에만 yield
                if item.get('title') and item.get('additional_data'):  # 필수 필드 확인
                    self.total_items += 1
                    yield item
                
            except Exception as e:
                self.logger.error(f"행 처리 오류: {e}")
                continue  # 오류 발생 시 다음 행으로 진행

        # 다음 페이지 처리
        if total_results > current_collected and has_next:
            next_offset = offset + actual_row_count
            next_url = response.url.split('?')[0]
            
            # 다음 페이지 요청
            params = {
                'day': current_date,
                'offset': next_offset,
                'size': self.results_per_page
            }
            next_url = f"{next_url}?{urlencode(params)}"
            
            self.logger.info(f"다음 페이지로 이동: {calendar_type} - {current_date}")
            self.logger.info(f"다음 페이지 URL: {next_url}")
            self.logger.info(f"현재까지 수집: {current_collected}/{total_results} 항목 ({progress_percentage:.1f}%)")
            
            # 누락된 행이 있다면 로그에 기록
            if missing_rows:
                self.logger.warning(f"현재 페이지에서 누락된 행: {sorted(list(missing_rows))}")
            
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                errback=self.errback_httpbin,
                headers=self.custom_headers,
                meta={
                    'calendar_type': calendar_type,
                    'date': current_date,
                    'offset': next_offset,
                    'current_date': current_date,
                    'total_expected': total_results,
                    'missing_rows_previous': list(missing_rows) if missing_rows else []
                },
                dont_filter=True  # URL 중복 필터링 비활성화
            )
    
    def closed(self, reason):
        """
        스파이더가 종료될 때 호출되는 메서드
        """
        self.logger.info("=" * 50)
        self.logger.info("수집 완료 보고서")
        self.logger.info("=" * 50)
        
        for cal_type, status in self.collection_status.items():
            total = status['total']
            collected = status['collected']
            completion = (collected / total * 100) if total > 0 else 0
            
            self.logger.info(
                f"{cal_type.upper()}: {collected}/{total} 항목 수집 "
                f"({completion:.1f}% 완료)"
            )
        
        self.logger.info("=" * 50)
        self.logger.info(f"총 수집 항목 수: {self.total_items}개") 