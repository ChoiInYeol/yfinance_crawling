# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class YfinanceCalendarPipeline:
    """야후 파이낸스 캘린더 데이터 처리 파이프라인
    
    이 파이프라인은 다음과 같은 작업을 수행합니다:
    1. 필수 필드 검증 - 필수 데이터가 있는지 확인
    2. 데이터 정제 - 빈 문자열, 하이픈('-')을 None으로 변환
    3. 중복 방지 - 동일한 데이터가 중복으로 수집되지 않도록 함
    
    Attributes:
        seen_items (set): 이미 처리한 항목의 키를 저장하는 집합
    """
    
    def __init__(self):
        """파이프라인 초기화 - 중복 방지 집합 생성"""
        # 중복 방지를 위한 키 집합
        self.seen_items = set()
    
    def process_item(self, item, spider):
        """
        아이템 처리 - 유효성 검사, 정제, 중복 제거
        
        Args:
            item (YFinanceCalendarItem): 처리할 아이템
            spider (Spider): 아이템을 생성한 스파이더
            
        Returns:
            YFinanceCalendarItem 또는 None: 유효한 아이템 또는 유효하지 않은 경우 None
        """
        adapter = ItemAdapter(item)
        
        # 필수 필드 검증 (calendar_type과 date만 필수로 변경)
        if not adapter.get('calendar_type') or not adapter.get('date'):
            spider.logger.warning(f"필수 필드 누락: {adapter.asdict()}")
            return None
        
        # 캘린더 타입별 필수 필드 검증 완화
        cal_type = adapter.get('calendar_type')
        additional_data = adapter.get('additional_data', {})
        
        if cal_type == 'earnings':
            # symbol이나 company 중 하나라도 있으면 허용
            if not additional_data.get('symbol') and not additional_data.get('company'):
                spider.logger.debug(f"earnings 항목에 식별 정보 누락: {adapter.asdict()}")
                return None
        
        elif cal_type == 'economic':
            # event나 country 중 하나라도 있으면 허용
            if not additional_data.get('event') and not additional_data.get('country'):
                spider.logger.debug(f"economic 항목에 식별 정보 누락: {adapter.asdict()}")
                return None
        
        elif cal_type == 'ipo':
            # symbol이나 company 중 하나라도 있으면 허용
            if not additional_data.get('symbol') and not additional_data.get('company'):
                spider.logger.debug(f"ipo 항목에 식별 정보 누락: {adapter.asdict()}")
                return None
        
        elif cal_type == 'splits':
            # symbol이나 company 중 하나라도 있으면 허용
            if not additional_data.get('symbol') and not additional_data.get('company'):
                spider.logger.debug(f"splits 항목에 식별 정보 누락: {adapter.asdict()}")
                return None
        
        # 데이터 정제 (빈 문자열, 하이픈('-') -> None으로 변환)
        for key, value in additional_data.items():
            if value in ['', '-', 'N/A', None]:
                additional_data[key] = None
        
        # 중복 방지 (캘린더 타입 + 식별자 + 날짜 기준)
        item_key = self._get_item_key(adapter)
        if item_key in self.seen_items:
            spider.logger.debug(f"중복 항목 무시: {item_key}")
            return None
        
        self.seen_items.add(item_key)
        return item
    
    def _get_item_key(self, adapter):
        """
        아이템의 고유 키를 생성
        
        Args:
            adapter (ItemAdapter): 아이템 어댑터
            
        Returns:
            str: 아이템 고유 키
        """
        cal_type = adapter.get('calendar_type')
        date = adapter.get('date')
        add_data = adapter.get('additional_data', {})
        
        if cal_type == 'earnings':
            # earnings: 'earnings:AAPL:2023-03-10'
            return f"{cal_type}:{add_data.get('symbol')}:{date}"
        elif cal_type == 'economic':
            # economic: 'economic:GDP:US:2023-03-10'
            return f"{cal_type}:{add_data.get('event')}:{add_data.get('country')}:{date}"
        elif cal_type == 'ipo':
            # ipo: 'ipo:AAPL:2023-03-10'
            return f"{cal_type}:{add_data.get('symbol')}:{date}"
        elif cal_type == 'splits':
            # splits: 'splits:AAPL:2023-03-10'
            return f"{cal_type}:{add_data.get('symbol')}:{date}"
        else:
            # 기타: 'other:title:2023-03-10'
            return f"{cal_type}:{adapter.get('title')}:{date}"
