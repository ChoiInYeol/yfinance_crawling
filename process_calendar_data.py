#!/usr/bin/env python
"""
Yahoo Finance 캘린더 데이터 처리 스크립트

이 스크립트는 다음 기능을 제공합니다:
1. 캘린더 데이터 수집 및 JSON 파일 저장 (캘린더 타입별로 분리)
2. 날짜 범위 지정 기능
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from yfinance_calendar.utils import generate_filename, process_calendar_data

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = os.path.join(PROJECT_ROOT, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'calendar_crawler_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def parse_args():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(description='Yahoo Finance 캘린더 데이터 처리')
    
    parser.add_argument('--start-date', type=str,
                      help='시작일 (YYYY-MM-DD 형식)')
    parser.add_argument('--end-date', type=str,
                      help='종료일 (YYYY-MM-DD 형식)')
    parser.add_argument('--output', type=str,
                      help='출력 파일명 접두사 (기본값: 현재 시각 기반 자동 생성)')
    
    return parser.parse_args()

def get_date_range(start_date=None, end_date=None):
    """날짜 범위 계산
    
    Args:
        start_date (str, optional): 시작일 (YYYY-MM-DD)
        end_date (str, optional): 종료일 (YYYY-MM-DD)
    
    Returns:
        tuple: (시작일, 종료일) - datetime 객체
    """
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start = datetime.now()
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = start + timedelta(days=7)
    
    # 미래 날짜 제한 (현재부터 1년)
    max_future = datetime.now() + timedelta(days=365)
    if end > max_future:
        end = max_future
        logging.warning(f'종료일이 최대 허용 기간을 초과하여 {max_future.strftime("%Y-%m-%d")}로 제한됩니다.')
    
    return start, end

def run_scrapy_command(cmd):
    """Scrapy 명령어 실행 및 결과 로깅
    
    Args:
        cmd (str): 실행할 명령어
    
    Returns:
        int: 실행 결과 코드
    """
    # Windows에서 실행 가능한 형태로 명령어 변환
    spider_dir = os.path.join(PROJECT_ROOT, "yfinance_calendar")
    if sys.platform == 'win32':
        cmd = f'cd "{spider_dir}" && python -m scrapy {cmd}'
    else:
        cmd = f'cd "{spider_dir}" && python -m scrapy {cmd}'
    
    logging.info(f'Scrapy 명령어 실행: {cmd}')
    result = os.system(cmd)
    if result == 0:
        logging.info('Scrapy 크롤링 완료')
    else:
        logging.error(f'Scrapy 크롤링 실패 (종료 코드: {result})')
    return result

def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging()
    logging.info('캘린더 데이터 수집 시작')
    
    args = parse_args()
    
    # 날짜 범위 계산
    start_date, end_date = get_date_range(args.start_date, args.end_date)
    logging.info(f'수집 기간: {start_date.strftime("%Y-%m-%d")} ~ {end_date.strftime("%Y-%m-%d")}')
    
    # 임시 JSON 파일명 생성
    temp_file = 'temp_calendar_data.json'
    
    # 출력 디렉토리 확인 및 생성
    output_dir = os.path.join(PROJECT_ROOT, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f'출력 디렉토리 생성: {output_dir}')
    
    # Scrapy 명령어 생성
    cmd_parts = ['crawl', 'yahoo_calendar', '-L', 'DEBUG']
    cmd_parts.extend(['-a', f'start_date={start_date.strftime("%Y-%m-%d")}'])
    cmd_parts.extend(['-a', f'end_date={end_date.strftime("%Y-%m-%d")}'])
    cmd_parts.extend(['-o', os.path.join(output_dir, temp_file), '-t', 'json'])
    
    # Scrapy 실행
    if run_scrapy_command(' '.join(cmd_parts)) != 0:
        logging.error('크롤링 중 오류가 발생하여 프로그램을 종료합니다.')
        return
    
    try:
        # JSON 파일 읽기
        json_path = os.path.join(output_dir, temp_file)
        if not os.path.exists(json_path):
            logging.error(f'JSON 파일이 생성되지 않았습니다: {json_path}')
            return
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logging.info(f'수집된 전체 데이터 수: {len(data)}개')
        
        # 데이터 처리
        processed_data = process_calendar_data(data)
        
        # 캘린더 타입별 데이터 수 로깅
        for cal_type, items in processed_data.items():
            logging.info(f'{cal_type} 데이터 수: {len(items)}개')
        
        # 파일명 접두사 설정
        base_name = args.output if args.output else generate_filename(extension='')[:-1]
        
        # 각 캘린더 타입별로 JSON 파일 저장
        for cal_type, items in processed_data.items():
            if items:  # 데이터가 있는 경우에만 파일 생성
                output_file = os.path.join(output_dir, f"{base_name}_{cal_type}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                logging.info(f'파일 저장 완료: {output_file}')
    
    except json.JSONDecodeError:
        logging.error('JSON 파일 파싱 중 오류가 발생했습니다.')
        logging.error('미래 날짜의 데이터는 제한될 수 있습니다.')
    
    except Exception as e:
        logging.error(f'처리 중 오류 발생: {str(e)}')
    
    finally:
        # 임시 파일 삭제
        temp_path = os.path.join(output_dir, temp_file)
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logging.info('임시 파일 삭제 완료')
    
    logging.info('캘린더 데이터 수집 완료')

if __name__ == '__main__':
    main() 