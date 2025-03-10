#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from shiny import App, render, ui, reactive
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def setup_database():
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    
    # 주가 데이터 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_prices (
        ticker TEXT,
        date DATE,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        market_cap REAL,
        PRIMARY KEY (ticker, date)
    )
    ''')
    
    conn.commit()
    return conn

def fetch_stock_data(ticker, start_date, end_date):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        df['market_cap'] = stock.info.get('marketCap', np.nan)
        df['ticker'] = ticker
        df.index.name = 'date'
        return df.reset_index()
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

def calculate_metrics(df):
    if df is None or df.empty:
        return None
    
    metrics = {
        'daily_returns': df['close'].pct_change(),
        'volatility': df['close'].pct_change().std() * np.sqrt(252),
        'sharpe_ratio': (df['close'].pct_change().mean() * 252) / (df['close'].pct_change().std() * np.sqrt(252)),
        'max_drawdown': (df['close'] / df['close'].cummax() - 1).min(),
        'avg_volume': df['volume'].mean(),
        'market_cap': df['market_cap'].iloc[0]
    }
    return metrics

# UI 정의
app_ui = ui.page_fluid(
    ui.panel_title("주식 분석 대시보드"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_text("ticker", "티커 심볼", value="AAPL"),
            ui.input_date_range("date_range", "기간 선택",
                              start=datetime.now() - timedelta(days=365),
                              end=datetime.now()),
            ui.input_select("metric", "분석 지표",
                          choices=["daily_returns", "volatility", "sharpe_ratio",
                                 "max_drawdown", "avg_volume"]),
            width=3
        ),
        ui.panel_main(
            ui.row(
                ui.column(6, ui.output_plot("price_chart")),
                ui.column(6, ui.output_plot("metric_chart"))
            ),
            ui.row(
                ui.column(12, ui.output_table("metrics_table"))
            )
        )
    )
)

# 서버 로직
def server(input, output, session):
    @reactive.Calc
    def stock_data():
        df = fetch_stock_data(
            input.ticker(),
            input.date_range()[0],
            input.date_range()[1]
        )
        return df
    
    @output
    @render.plot
    def price_chart():
        df = stock_data()
        if df is None:
            return None
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC'
        ))
        
        fig.update_layout(
            title=f"{input.ticker()} 주가 차트",
            yaxis_title="가격",
            template='plotly_white'
        )
        return fig
    
    @output
    @render.plot
    def metric_chart():
        df = stock_data()
        if df is None:
            return None
        
        metrics = calculate_metrics(df)
        if metrics is None:
            return None
        
        selected_metric = input.metric()
        if selected_metric == 'daily_returns':
            fig = px.line(df, x='date', y='close', title='일별 수익률')
        else:
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=metrics[selected_metric],
                title={'text': selected_metric.replace('_', ' ').title()}
            ))
        
        return fig
    
    @output
    @render.table
    def metrics_table():
        df = stock_data()
        if df is None:
            return None
        
        metrics = calculate_metrics(df)
        if metrics is None:
            return None
        
        metrics_df = pd.DataFrame({
            '지표': [k.replace('_', ' ').title() for k in metrics.keys()],
            '값': [f"{v:.4f}" if isinstance(v, float) else f"{v:,.0f}" for v in metrics.values()]
        })
        return metrics_df

app = App(app_ui, server)

if __name__ == "__main__":
    app.run() 