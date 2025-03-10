#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from datetime import datetime, timedelta

def load_market_cap_data():
    """시가총액 데이터 로드"""
    return pd.read_csv('db/market_caps.csv')

def load_stock_price_data(ticker):
    """주가 데이터 로드"""
    file_path = f'db/stock_prices_{ticker}.csv'
    if os.path.exists(file_path):
        return pd.read_csv(file_path, index_col=0, parse_dates=True)
    return None

def create_market_cap_chart(market_cap_df):
    """시가총액 차트 생성"""
    fig = go.Figure(data=[
        go.Bar(
            x=market_cap_df['Symbol'],
            y=market_cap_df['Market_Cap'],
            text=[f"${cap:,.0f}" for cap in market_cap_df['Market_Cap']],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="시가총액 상위 티커",
        xaxis_title="티커",
        yaxis_title="시가총액 (USD)",
        template='plotly_white'
    )
    return fig

def load_event_dates():
    """이벤트 날짜 정보 로드"""
    try:
        # Excel 파일에서 Earnings 시트 로드
        df = pd.read_excel('event_analysis.xlsx', sheet_name='Earnings')
        
        # 날짜 컬럼을 datetime으로 변환
        df['date'] = pd.to_datetime(df['date'])
        
        # 필요한 컬럼만 선택
        event_info = df[['Symbol', 'date', 'Company', 'Event Name', 'Earnings Call Time', 'EPS Estimate', 'Reported EPS', 'Surprise (%)']]
        
        # 날짜 정보를 딕셔너리로 변환
        event_dates = dict(zip(event_info['Symbol'], event_info['date']))
        
        # 이벤트 상세 정보를 딕셔너리로 변환
        event_details = {}
        for _, row in event_info.iterrows():
            event_details[row['Symbol']] = {
                'date': row['date'],
                'company_name': row['Company'],
                'event_name': row['Event Name'],
                'call_time': row['Earnings Call Time'],
                'eps_estimate': row['EPS Estimate'],
                'reported_eps': row['Reported EPS'],
                'surprise': row['Surprise (%)']
            }
        
        print(f"총 {len(event_dates)}개의 이벤트 날짜 정보 로드됨")
        return event_dates, event_details
    except Exception as e:
        print(f"이벤트 날짜 정보 로드 중 오류 발생: {e}")
        return {}, {}

def create_event_performance_chart(market_cap_df, event_dates, event_details):
    """이벤트 성과 차트 생성 (이전 3개월 + 이후)"""
    fig = go.Figure()
    
    # 상위 10개 티커만 선택
    top_tickers = market_cap_df.nlargest(10, 'Market_Cap')['Symbol'].tolist()
    
    for ticker in top_tickers:
        if ticker not in event_dates:
            continue
            
        price_df = load_stock_price_data(ticker)
        if price_df is None:
            continue
            
        event_date = event_dates[ticker]
        if event_date not in price_df.index:
            continue
            
        # 이벤트 날짜 기준으로 정규화
        event_price = price_df.loc[event_date, 'Close']
        normalized_prices = price_df['Close'] / event_price - 1
        
        # 이벤트 이전 3개월부터 이후 1개월까지 선택
        pre_event_date = event_date - pd.DateOffset(months=3)
        post_event_date = event_date + pd.DateOffset(months=1)
        analysis_data = normalized_prices[
            (price_df.index >= pre_event_date) & 
            (price_df.index <= post_event_date)
        ]
        
        # 이벤트 시점 표시를 위한 수직선 추가
        fig.add_shape(
            type="line",
            x0=event_date,
            x1=event_date,
            y0=analysis_data.min(),
            y1=analysis_data.max(),
            line=dict(color="red", dash="dash"),
            xref="x",
            yref="y"
        )
        
        # 이벤트 정보 텍스트 박스 추가
        event_info = event_details[ticker]
        info_text = f"{event_info['company_name']}<br>"
        info_text += f"Event: {event_info['event_name']}<br>"
        info_text += f"EPS: {event_info['reported_eps']} (Est: {event_info['eps_estimate']})<br>"
        info_text += f"Surprise: {event_info['surprise']}%"
        
        fig.add_annotation(
            x=event_date,
            y=analysis_data.max(),
            text=info_text,
            showarrow=True,
            arrowhead=1,
            font=dict(size=10),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='black',
            borderwidth=1
        )
        
        fig.add_trace(go.Scatter(
            x=analysis_data.index,
            y=analysis_data.values,
            name=f"{ticker} ({event_date.strftime('%Y-%m-%d')})",
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title="Event Stock Performance (3M Before + 1M After)",
        xaxis_title="Date",
        yaxis_title="Price Change vs Event",
        template='plotly_white',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def create_event_summary_table(market_cap_df, event_dates, event_details):
    """이벤트 성과 요약 테이블 생성"""
    summary_data = []
    
    # 상위 20개 티커만 선택
    top_tickers = market_cap_df.nlargest(20, 'Market_Cap')['Symbol'].tolist()
    
    for ticker in top_tickers:
        if ticker not in event_dates:
            continue
            
        market_cap = market_cap_df[market_cap_df['Symbol'] == ticker]['Market_Cap'].iloc[0]
        price_df = load_stock_price_data(ticker)
        if price_df is None:
            continue
            
        event_date = event_dates[ticker]
        if event_date not in price_df.index:
            continue
            
        # 이벤트 날짜 기준으로 정규화
        event_price = price_df.loc[event_date, 'Close']
        normalized_prices = price_df['Close'] / event_price - 1
        
        # 이벤트 이전 3개월부터 이후 1개월까지 선택
        pre_event_date = event_date - pd.DateOffset(months=3)
        post_event_date = event_date + pd.DateOffset(months=1)
        analysis_data = normalized_prices[
            (price_df.index >= pre_event_date) & 
            (price_df.index <= post_event_date)
        ]
        
        # 성과 지표 계산
        pre_event_return = normalized_prices[pre_event_date:event_date].iloc[-1]
        post_event_return = normalized_prices[event_date:post_event_date].iloc[-1]
        total_return = normalized_prices[pre_event_date:post_event_date].iloc[-1]
        
        # 변동성 계산 (이벤트 이후 1개월)
        post_event_volatility = normalized_prices[event_date:post_event_date].std() * np.sqrt(252)
        
        # 최대 낙폭 계산 (이벤트 이후 1개월)
        post_event_data = normalized_prices[event_date:post_event_date]
        max_drawdown = (post_event_data.cummax() - post_event_data) / post_event_data.cummax()
        max_drawdown = max_drawdown.max()
        
        # 거래량 변화
        pre_event_volume = price_df[pre_event_date:event_date].Volume.mean()
        post_event_volume = price_df[event_date:post_event_date].Volume.mean()
        volume_change = (post_event_volume / pre_event_volume - 1)
        
        # 이벤트 정보
        event_info = event_details[ticker]
        
        summary_data.append({
            'Ticker': ticker,
            'Company': event_info['company_name'],
            'Event': event_info['event_name'],
            'Event Date': event_date.strftime('%Y-%m-%d'),
            'Market Cap': f"${market_cap:,.0f}",
            'EPS': f"{event_info['reported_eps']} (Est: {event_info['eps_estimate']})",
            'Surprise': f"{event_info['surprise']}%",
            'Pre-Event Return': f"{pre_event_return:.2%}",
            'Post-Event Return': f"{post_event_return:.2%}",
            'Total Return': f"{total_return:.2%}",
            'Post-Event Vol': f"{post_event_volatility:.2%}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Volume Change': f"{volume_change:.2%}"
        })
    
    return pd.DataFrame(summary_data)

def main():
    # 데이터 로드
    market_cap_df = load_market_cap_data()
    event_dates, event_details = load_event_dates()
    
    if not event_dates:
        print("이벤트 날짜 정보를 찾을 수 없습니다.")
        return
    
    # 차트 생성
    market_cap_fig = create_market_cap_chart(market_cap_df)
    performance_fig = create_event_performance_chart(market_cap_df, event_dates, event_details)
    summary_df = create_event_summary_table(market_cap_df, event_dates, event_details)
    
    # HTML 파일로 저장
    with open('event_stock_analysis.html', 'w', encoding='utf-8') as f:
        f.write('<html><head><title>Event Stock Analysis</title></head><body>')
        f.write('<h1>Event Stock Analysis</h1>')
        
        # 시가총액 차트
        f.write('<h2>Market Cap Top Tickers</h2>')
        f.write(market_cap_fig.to_html(full_html=False))
        
        # 이벤트 성과 차트
        f.write('<h2>Event Stock Performance (3M Before + 1M After)</h2>')
        f.write(performance_fig.to_html(full_html=False))
        
        # 요약 테이블
        f.write('<h2>Event Performance Summary</h2>')
        f.write(summary_df.to_html())
        
        f.write('</body></html>')
    
    print("분석 결과가 'event_stock_analysis.html' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main() 