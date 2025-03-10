"""
Yahoo Finance 캘린더 데이터 처리 유틸리티
"""
import pandas as pd

def process_earnings_data(items):
    """실적 발표 데이터 처리"""
    processed = []
    for item in items:
        additional = item.get('additional_data', {})
        processed_item = {
            'symbol': additional.get('symbol', ''),
            'company': additional.get('company', ''),
            'event_name': additional.get('event_name', ''),
            'date': item.get('date', ''),
            'call_time': additional.get('call_time', ''),
            'eps_estimate': additional.get('eps_estimate', ''),
            'reported_eps': additional.get('reported_eps', ''),
            'surprise': additional.get('surprise', '')
        }
        processed.append(processed_item)
    return sorted(processed, key=lambda x: x['date'])

def process_economic_data(items):
    """경제 지표 데이터 처리"""
    processed = []
    for item in items:
        additional = item.get('additional_data', {})
        processed_item = {
            'event': additional.get('event', ''),
            'country': additional.get('country', ''),
            'date': item.get('date', ''),
            'event_time': additional.get('event_time', ''),
            'event_for': additional.get('event_for', ''),
            'actual': additional.get('actual', ''),
            'market_expectation': additional.get('market_expectation', ''),
            'prior': additional.get('prior', ''),
            'revised_from': additional.get('revised_from', '')
        }
        processed.append(processed_item)
    return sorted(processed, key=lambda x: x['date'])

def process_ipo_data(items):
    """IPO 데이터 처리"""
    processed = []
    for item in items:
        additional = item.get('additional_data', {})
        processed_item = {
            'symbol': additional.get('symbol', ''),
            'company': additional.get('company', ''),
            'exchange': additional.get('exchange', ''),
            'date': item.get('date', ''),
            'ipo_date': additional.get('ipo_date', ''),
            'price_range': additional.get('price_range', ''),
            'price': additional.get('price', ''),
            'currency': additional.get('currency', ''),
            'shares': additional.get('shares', ''),
            'actions': additional.get('actions', '')
        }
        processed.append(processed_item)
    return sorted(processed, key=lambda x: x['date'])

def process_splits_data(items):
    """주식 분할 데이터 처리"""
    processed = []
    for item in items:
        additional = item.get('additional_data', {})
        processed_item = {
            'symbol': additional.get('symbol', ''),
            'company': additional.get('company', ''),
            'date': item.get('date', ''),
            'payable_on': additional.get('payable_on', ''),
            'optionable': additional.get('optionable', ''),
            'ratio': additional.get('ratio', '')
        }
        processed.append(processed_item)
    return sorted(processed, key=lambda x: x['date'])

def process_calendar_data(data):
    """캘린더 데이터 처리"""
    calendar_types = {
        'earnings': [],
        'economic': [],
        'ipo': [],
        'splits': []
    }
    
    for item in data:
        cal_type = item.get('calendar_type')
        if cal_type in calendar_types:
            calendar_types[cal_type].append(item)
    
    processed_data = {
        'earnings': process_earnings_data(calendar_types['earnings']),
        'economic': process_economic_data(calendar_types['economic']),
        'ipo': process_ipo_data(calendar_types['ipo']),
        'splits': process_splits_data(calendar_types['splits'])
    }
    
    return processed_data

def json_to_dataframe(json_file):
    """JSON 파일을 pandas DataFrame으로 변환
    
    Args:
        json_file (str): JSON 파일 경로
    
    Returns:
        dict: 캘린더 타입별 DataFrame을 담은 딕셔너리
    """
    import json
    
    # JSON 파일 읽기
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 캘린더 타입별로 데이터 분리
    calendar_types = {}
    for item in data:
        cal_type = item['calendar_type']
        if cal_type not in calendar_types:
            calendar_types[cal_type] = []
        calendar_types[cal_type].append(item)
    
    # 캘린더 타입별 DataFrame 생성
    processors = {
        'earnings': process_earnings_data,
        'economic': process_economic_data,
        'ipo': process_ipo_data,
        'splits': process_splits_data
    }
    
    dataframes = {}
    for cal_type, items in calendar_types.items():
        if cal_type in processors:
            dataframes[cal_type] = pd.DataFrame(processors[cal_type](items))
    
    return dataframes 