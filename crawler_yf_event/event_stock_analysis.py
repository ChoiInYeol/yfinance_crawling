#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, render, ui, reactive

def load_event_data(file_path):
    """이벤트 데이터 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def get_top_tickers(df, n=10):
    """시가총액 기준 상위 티커 추출"""
    tickers = df[df['event_type'] == 'earnings']['Symbol'].unique()
    market_caps = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            market_cap = stock.info.get('marketCap', 0)
            market_caps[ticker] = market_cap
        except:
            market_caps[ticker] = 0
    
    return sorted(market_caps.items(), key=lambda x: x[1], reverse=True)[:n]

def analyze_event_impact(ticker, event_date, window=5):
    """이벤트 전후 주가 변화 분석"""
    try:
        stock = yf.Ticker(ticker)
        start_date = event_date - timedelta(days=window)
        end_date = event_date + timedelta(days=window)
        
        df = stock.history(start=start_date, end=end_date)
        if df.empty:
            return None
        
        # 이벤트일 기준으로 정규화
        event_price = df.loc[event_date, 'Close']
        df['Normalized_Price'] = df['Close'] / event_price - 1
        
        return df
    except:
        return None

def create_event_analysis_dashboard():
    # UI 정의
    app_ui = ui.page_fluid(
        ui.panel_title("이벤트 기반 주가 분석 대시보드"),
        ui.layout_sidebar(
            ui.panel_sidebar(
                ui.input_select("event_type", "이벤트 타입",
                              choices=["earnings", "economic", "ipo", "splits"]),
                ui.input_numeric("top_n", "상위 티커 수", value=5, min=1, max=20),
                ui.input_numeric("window", "분석 기간 (일)", value=5, min=1, max=30),
                width=3
            ),
            ui.panel_main(
                ui.row(
                    ui.column(12, ui.output_plot("market_cap_chart"))
                ),
                ui.row(
                    ui.column(12, ui.output_plot("event_impact_chart"))
                ),
                ui.row(
                    ui.column(12, ui.output_table("event_summary"))
                )
            )
        )
    )
    
    # 서버 로직
    def server(input, output, session):
        @reactive.Calc
        def event_data():
            df = load_event_data('yf_calendar_events.json')
            df['date'] = pd.to_datetime(df['date'])
            return df
        
        @reactive.Calc
        def top_tickers():
            df = event_data()
            return get_top_tickers(df, input.top_n())
        
        @output
        @render.plot
        def market_cap_chart():
            tickers = top_tickers()
            if not tickers:
                return None
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[t[0] for t in tickers],
                    y=[t[1] for t in tickers],
                    text=[f"${t[1]:,.0f}" for t in tickers],
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
        
        @output
        @render.plot
        def event_impact_chart():
            df = event_data()
            tickers = top_tickers()
            if not tickers:
                return None
            
            fig = go.Figure()
            for ticker, _ in tickers:
                ticker_events = df[
                    (df['event_type'] == input.event_type()) & 
                    (df['Symbol'] == ticker)
                ]
                
                for _, event in ticker_events.iterrows():
                    impact_df = analyze_event_impact(
                        ticker, 
                        event['date'], 
                        input.window()
                    )
                    if impact_df is not None:
                        fig.add_trace(go.Scatter(
                            x=impact_df.index,
                            y=impact_df['Normalized_Price'],
                            name=f"{ticker} ({event['date'].strftime('%Y-%m-%d')})",
                            mode='lines+markers'
                        ))
            
            fig.update_layout(
                title=f"{input.event_type().capitalize()} 이벤트 주가 영향",
                xaxis_title="이벤트 기준 일수",
                yaxis_title="정규화된 가격 변화",
                template='plotly_white'
            )
            return fig
        
        @output
        @render.table
        def event_summary():
            df = event_data()
            tickers = top_tickers()
            if not tickers:
                return None
            
            summary_data = []
            for ticker, market_cap in tickers:
                ticker_events = df[
                    (df['event_type'] == input.event_type()) & 
                    (df['Symbol'] == ticker)
                ]
                
                for _, event in ticker_events.iterrows():
                    impact_df = analyze_event_impact(
                        ticker, 
                        event['date'], 
                        input.window()
                    )
                    if impact_df is not None:
                        pre_event = impact_df['Normalized_Price'].iloc[0]
                        post_event = impact_df['Normalized_Price'].iloc[-1]
                        summary_data.append({
                            '티커': ticker,
                            '이벤트일': event['date'].strftime('%Y-%m-%d'),
                            '시가총액': f"${market_cap:,.0f}",
                            '사전 변화': f"{pre_event:.2%}",
                            '사후 변화': f"{post_event:.2%}",
                            '순 변화': f"{(post_event - pre_event):.2%}"
                        })
            
            return pd.DataFrame(summary_data)
    
    return App(app_ui, server)

if __name__ == "__main__":
    app = create_event_analysis_dashboard()
    app.run() 