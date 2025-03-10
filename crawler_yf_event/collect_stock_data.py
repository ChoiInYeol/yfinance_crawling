#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import json
from tqdm import tqdm
import time
import FinanceDataReader as fdr

def create_db_directory():
    """db 디렉토리 생성"""
    if not os.path.exists('db'):
        os.makedirs('db')

def load_event_data(file_path):
    """이벤트 데이터 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def get_us_market_tickers():
    """미국 시장 종목 목록 가져오기"""
    print("미국 시장 종목 목록 수집 중...")
    
    # S&P500 종목 목록만 수집
    sp500 = fdr.StockListing('S&P500')
    us_tickers = set(sp500['Symbol'].tolist())
    print(f"총 {len(us_tickers)}개의 미국 시장 종목 발견")
    
    return list(us_tickers)

def collect_market_cap_data(df, n=10):
    """시가총액 데이터 수집"""
    # 미국 시장 종목 필터링
    us_tickers = get_us_market_tickers()
    
    # 이벤트 데이터에서 미국 시장 종목만 필터링
    event_tickers = df[df['event_type'] == 'earnings']['Symbol'].unique()
    filtered_tickers = [ticker for ticker in event_tickers if ticker in us_tickers]
    print(f"필터링 후 {len(filtered_tickers)}개의 종목 선택됨")
    
    try:
        # 모든 종목 한 번에 처리
        print("시가총액 데이터 수집 중...")
        stocks = yf.Tickers(filtered_tickers)
        
        # 시가총액 데이터 수집
        market_caps = {}
        for ticker in filtered_tickers:
            market_cap = stocks.tickers[ticker].info.get('marketCap', 0)
            market_caps[ticker] = market_cap
        
        # 상위 n개 티커 선택
        top_tickers = sorted(market_caps.items(), key=lambda x: x[1], reverse=True)[:n]
        
        # DataFrame 생성 및 저장
        market_cap_df = pd.DataFrame(top_tickers, columns=['Symbol', 'Market_Cap'])
        market_cap_df.to_csv('db/market_caps.csv', index=False)
        
        return market_cap_df
    except Exception as e:
        print(f"\n시가총액 데이터 수집 중 오류 발생: {e}")
        return None

def collect_stock_price_data():
    """주가 데이터 수집 (최근 1년)"""
    # market_caps.csv에서 상위 종목 목록 로드
    market_cap_df = pd.read_csv('db/market_caps.csv')
    top_tickers = market_cap_df['Symbol'].tolist()
    print(f"시가총액 상위 {len(top_tickers)}개 종목의 주가 데이터 수집 시작")
    
    # 날짜 범위 설정 (최근 1년)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        # 모든 종목 한 번에 다운로드
        print("주가 데이터 다운로드 중...")
        price_df = yf.download(top_tickers, start=start_date, end=end_date)
        
        # 각 티커별로 데이터 분리 및 저장
        for ticker in top_tickers:
            if ticker in price_df.columns.get_level_values(1):
                ticker_data = price_df.xs(ticker, axis=1, level=1)
                if not ticker_data.empty:
                    # 종가 기준으로 정규화
                    ticker_data['Normalized_Price'] = ticker_data['Close'] / ticker_data['Close'].iloc[0] - 1
                    # 데이터 저장
                    ticker_data.to_csv(f'db/stock_prices_{ticker}.csv')
                    print(f"{ticker} 데이터 저장 완료")
        
        return price_df
    except Exception as e:
        print(f"\n데이터 다운로드 중 오류 발생: {e}")
        return None

def main():
    start_time = time.time()
    
    # db 디렉토리 생성
    create_db_directory()
    
    # 이벤트 데이터 로드
    print("이벤트 데이터 로드 중...")
    df = load_event_data('yf_calendar_events.json')
    print(f"총 {len(df)}개의 이벤트 데이터 로드됨")
    
    # 시가총액 데이터 수집
    print("\n시가총액 데이터 수집 중...")
    market_cap_df = collect_market_cap_data(df, n=10)
    print(f"상위 {len(market_cap_df)}개 티커의 시가총액 데이터 수집 완료")
    
    # 주가 데이터 수집
    print("\n주가 데이터 수집 중...")
    price_data = collect_stock_price_data()
    print(f"{len(price_data)}개 티커의 주가 데이터 수집 완료")
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print("\n데이터 수집이 완료되었습니다.")
    print(f"총 실행 시간: {execution_time:.2f}초")
    print(f"- 시가총액 데이터: db/market_caps.csv")
    print(f"- 주가 데이터: db/stock_prices_*.csv")

if __name__ == "__main__":
    main() 