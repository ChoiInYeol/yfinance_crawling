#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler_yf_event.spiders.yf_calendar_spider import YFCalendarSpider

def run_crawler(start_date=None, end_date=None, events=None, days=20):
    """
    Yahoo Finance 이벤트 크롤러를 실행하는 함수
    
    Args:
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식)
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식)
        events (list, optional): 수집할 이벤트 타입 리스트
        days (int, optional): 현재 날짜 기준 전후 수집할 일수
    """
    # 프로젝트 설정 가져오기
    settings = get_project_settings()
    
    # 크롤러 프로세스 생성
    process = CrawlerProcess(settings)
    
    # 날짜 설정
    today = datetime.now()
    if not start_date:
        start_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = (today + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 이벤트 타입 설정
    if not events:
        events = ['earnings', 'economic', 'ipo', 'splits']
    
    # 크롤러 실행
    process.crawl(
        YFCalendarSpider,
        start_date=start_date,
        end_date=end_date,
        events=','.join(events)
    )
    process.start()

if __name__ == "__main__":
    # 커맨드 라인 인자 처리
    import argparse
    parser = argparse.ArgumentParser(description='Yahoo Finance 이벤트 크롤러 실행')
    parser.add_argument('--start-date', type=str, help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--events', type=str, help='수집할 이벤트 타입 (쉼표로 구분)')
    parser.add_argument('--days', type=int, default=7, help='현재 날짜 기준 전후 수집할 일수')
    
    args = parser.parse_args()
    
    # 이벤트 타입 처리
    events = args.events.split(',') if args.events else None
    
    # 크롤러 실행
    run_crawler(
        start_date=args.start_date,
        end_date=args.end_date,
        events=events,
        days=args.days
    ) 