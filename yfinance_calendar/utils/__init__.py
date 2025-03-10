"""
Yahoo Finance 캘린더 유틸리티 패키지
"""
from datetime import datetime
from typing import Optional
from .data_processor import (
    process_calendar_data,
    process_earnings_data,
    process_economic_data,
    process_ipo_data,
    process_splits_data,
    json_to_dataframe
)

def generate_filename(
    calendar_type: Optional[str] = None,
    date_str: Optional[str] = None,
    prefix: str = 'calendar_data',
    extension: str = 'json'
) -> str:
    """
    캘린더 데이터 파일 이름을 생성합니다.
    
    Args:
        calendar_type (str, optional): 캘린더 타입 (earnings, economic, ipo, splits)
        date_str (str, optional): 날짜 문자열 (YYYY-MM-DD)
        prefix (str, optional): 파일명 접두사. Defaults to 'calendar_data'.
        extension (str, optional): 파일 확장자. Defaults to 'json'.
        
    Returns:
        str: 생성된 파일 이름
        
    Examples:
        >>> generate_filename(calendar_type='earnings', date_str='2024-03-10')
        'earnings_20240310.json'
        >>> generate_filename(prefix='data', extension='csv')
        'data_20240310_191140.csv'
    """
    if calendar_type and date_str:
        try:
            # 캘린더 타입과 날짜가 주어진 경우
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return f"{calendar_type}_{date_obj.strftime('%Y%m%d')}.{extension}"
        except ValueError as e:
            raise ValueError(f"잘못된 날짜 형식입니다: {date_str}") from e
    else:
        # 기존 방식: 현재 시각 기반 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"

__all__ = [
    'generate_filename',
    'process_calendar_data',
    'process_earnings_data',
    'process_economic_data',
    'process_ipo_data',
    'process_splits_data',
    'json_to_dataframe'
]
