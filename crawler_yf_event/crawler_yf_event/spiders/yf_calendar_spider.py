import scrapy
from datetime import datetime, timedelta
import re
from ..items import YFCalendarEventItem
from urllib.parse import urljoin

class YFCalendarSpider(scrapy.Spider):
    name = 'yf_calendar'
    allowed_domains = ['finance.yahoo.com']
    
    def __init__(self, *args, **kwargs):
        super(YFCalendarSpider, self).__init__(*args, **kwargs)
        self.event_types = ['earnings', 'economic', 'ipo', 'splits']
        self.base_url = 'https://finance.yahoo.com/calendar/'
        
        # 커맨드 라인 인자 처리
        self.start_date = kwargs.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        self.end_date = kwargs.get('end_date', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        self.selected_events = kwargs.get('events', self.event_types)
        
        # 선택된 이벤트 타입만 필터링
        self.event_types = [event for event in self.event_types if event in self.selected_events]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        # 이벤트별 파일 저장을 위한 설정
        spider.event_files = {}
        return spider

    def start_requests(self):
        for event_type in self.event_types:
            url = f'{self.base_url}{event_type}'
            params = {
                'from': self.start_date,
                'to': self.end_date,
                'size': '100'  # 한 페이지당 100개 항목
            }
            yield scrapy.Request(
                url=f'{url}?{"&".join(f"{k}={v}" for k, v in params.items())}',
                callback=self.parse,
                meta={'event_type': event_type},
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
            )

    def parse(self, response):
        event_type = response.meta['event_type']
        
        # 전체 결과 수 추출
        results_text = response.xpath('//*[@id="nimbus-app"]/section/section/section/article/section/section[1]/div[1]/div/div/p/text()').get()
        total_results = 0
        if results_text:
            match = re.search(r'of (\d+) Results', results_text)
            if match:
                total_results = int(match.group(1))

        # 테이블 헤더 추출
        headers = response.xpath('//*[@id="nimbus-app"]/section/section/section/article/section/section[1]/div[2]/table/thead/tr/th')
        header_texts = [header.xpath('.//text()').get().strip() for header in headers if header.xpath('.//text()').get()]

        # 데이터 행 추출
        rows = response.xpath('//*[@id="nimbus-app"]/section/section/section/article/section/section[1]/div[2]/table/tbody/tr')
        
        for row in rows:
            item = YFCalendarEventItem()
            item['event_type'] = event_type
            item['crawl_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 각 열의 데이터 추출
            cells = row.xpath('.//td')
            for idx, cell in enumerate(cells):
                try:
                    # 헤더가 있는 경우에만 처리
                    if idx < len(header_texts):
                        header = header_texts[idx]
                        # economic 이벤트의 Event 칼럼 특별 처리
                        if event_type == 'economic' and header == 'Event':
                            value = cell.xpath('.//text()').get()
                        # Symbol과 Company Name은 특별 처리
                        elif idx == 0:  # Symbol
                            value = cell.xpath('.//a/text()').get()
                        elif idx == 1:  # Company Name
                            value = cell.xpath('.//text()').get()
                        else:
                            value = cell.xpath('.//text()').get()
                        
                        # 값이 있는 경우에만 저장
                        if value:
                            item[header] = value.strip()
                except Exception as e:
                    self.logger.error(f'Error processing cell at index {idx}: {str(e)}')
                    continue

            yield item

        # 다음 페이지 처리
        next_button = response.xpath('//*[@id="nimbus-app"]/section/section/section/article/section/section[1]/div[3]/div[3]/button[3]')
        if next_button and total_results > 100:
            current_url = response.url
            if 'offset=' in current_url:
                current_offset = int(re.search(r'offset=(\d+)', current_url).group(1))
                next_offset = current_offset + 100
                next_url = re.sub(r'offset=\d+', f'offset={next_offset}', current_url)
            else:
                next_url = f"{current_url}&offset=100"
            
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={'event_type': event_type},
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
            ) 