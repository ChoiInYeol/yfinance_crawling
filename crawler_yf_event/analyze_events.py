#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

def load_and_process_data(file_path):
    # JSON 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # DataFrame으로 변환
    df = pd.DataFrame(data)
    
    # 날짜 컬럼을 datetime으로 변환
    df['date'] = pd.to_datetime(df['date'])
    
    # 이벤트 타입별로 데이터프레임 분리
    earnings_df = df[df['event_type'] == 'earnings'].copy()
    economic_df = df[df['event_type'] == 'economic'].copy()
    ipo_df = df[df['event_type'] == 'ipo'].copy()
    splits_df = df[df['event_type'] == 'splits'].copy()
    
    return earnings_df, economic_df, ipo_df, splits_df

def create_visualizations(earnings_df, economic_df, ipo_df, splits_df):
    # 1. 일별 이벤트 수 시각화
    daily_counts = pd.DataFrame({
        'earnings': earnings_df.groupby('date').size(),
        'economic': economic_df.groupby('date').size(),
        'ipo': ipo_df.groupby('date').size(),
        'splits': splits_df.groupby('date').size()
    }).fillna(0)
    
    fig1 = go.Figure()
    for col in daily_counts.columns:
        fig1.add_trace(go.Scatter(
            x=daily_counts.index,
            y=daily_counts[col],
            name=col.capitalize(),
            mode='lines+markers'
        ))
    
    fig1.update_layout(
        title='일별 이벤트 수 추이',
        xaxis_title='날짜',
        yaxis_title='이벤트 수',
        template='plotly_white'
    )
    
    # 2. 경제 지표 국가별 분포
    if not economic_df.empty:
        country_counts = economic_df['Country'].value_counts()
        fig2 = px.pie(
            values=country_counts.values,
            names=country_counts.index,
            title='경제 지표 국가별 분포'
        )
    else:
        fig2 = go.Figure()
        fig2.add_annotation(text="경제 지표 데이터 없음")
    
    # 3. 실적 발표 시간대 분포
    if not earnings_df.empty:
        earnings_df['Earnings Call Time'] = earnings_df['Earnings Call Time'].fillna('Unknown')
        time_counts = earnings_df['Earnings Call Time'].value_counts()
        fig3 = px.bar(
            x=time_counts.index,
            y=time_counts.values,
            title='실적 발표 시간대 분포'
        )
    else:
        fig3 = go.Figure()
        fig3.add_annotation(text="실적 발표 데이터 없음")
    
    # 4. EPS Surprise 분포
    if not earnings_df.empty:
        earnings_df['Surprise (%)'] = pd.to_numeric(earnings_df['Surprise (%)'].str.replace('-', 'NaN'), errors='coerce')
        fig4 = px.histogram(
            earnings_df,
            x='Surprise (%)',
            title='EPS Surprise 분포',
            nbins=50
        )
    else:
        fig4 = go.Figure()
        fig4.add_annotation(text="실적 발표 데이터 없음")
    
    # 5. 경제 지표 시간대별 분포
    if not economic_df.empty:
        economic_df['Event Time'] = pd.to_datetime(economic_df['Event Time'], format='%I:%M %p UTC', errors='coerce')
        fig5 = px.histogram(
            economic_df,
            x='Event Time',
            title='경제 지표 발표 시간대 분포',
            nbins=24
        )
    else:
        fig5 = go.Figure()
        fig5.add_annotation(text="경제 지표 데이터 없음")
    
    return fig1, fig2, fig3, fig4, fig5

def main():
    # 데이터 로드
    earnings_df, economic_df, ipo_df, splits_df = load_and_process_data('yf_calendar_events.json')
    
    # 시각화 생성
    fig1, fig2, fig3, fig4, fig5 = create_visualizations(earnings_df, economic_df, ipo_df, splits_df)
    
    # Excel 파일로 저장
    with pd.ExcelWriter('event_analysis.xlsx', engine='openpyxl') as writer:
        earnings_df.to_excel(writer, sheet_name='Earnings', index=False)
        economic_df.to_excel(writer, sheet_name='Economic', index=False)
        ipo_df.to_excel(writer, sheet_name='IPO', index=False)
        splits_df.to_excel(writer, sheet_name='Splits', index=False)
        
        # 일별 이벤트 수 요약
        daily_counts = pd.DataFrame({
            'earnings': earnings_df.groupby('date').size(),
            'economic': economic_df.groupby('date').size(),
            'ipo': ipo_df.groupby('date').size(),
            'splits': splits_df.groupby('date').size()
        }).fillna(0)
        daily_counts.to_excel(writer, sheet_name='Daily_Summary')
    
    # HTML 파일로 저장
    with open('event_analysis.html', 'w', encoding='utf-8') as f:
        f.write('<html><head><title>Yahoo Finance 이벤트 분석</title></head><body>')
        f.write('<h1>Yahoo Finance 이벤트 분석</h1>')
        
        # 데이터 요약
        f.write('<h2>데이터 요약</h2>')
        summary = pd.DataFrame({
            '이벤트 타입': ['earnings', 'economic', 'ipo', 'splits'],
            '총 이벤트 수': [
                len(earnings_df),
                len(economic_df),
                len(ipo_df),
                len(splits_df)
            ]
        })
        f.write(summary.to_html())
        
        # 그래프 저장
        f.write('<h2>일별 이벤트 수 추이</h2>')
        f.write(fig1.to_html(full_html=False))
        
        f.write('<h2>경제 지표 국가별 분포</h2>')
        f.write(fig2.to_html(full_html=False))
        
        f.write('<h2>실적 발표 시간대 분포</h2>')
        f.write(fig3.to_html(full_html=False))
        
        f.write('<h2>EPS Surprise 분포</h2>')
        f.write(fig4.to_html(full_html=False))
        
        f.write('<h2>경제 지표 발표 시간대 분포</h2>')
        f.write(fig5.to_html(full_html=False))
        
        f.write('</body></html>')
    
    print("분석 결과가 'event_analysis.html' 및 'event_analysis.xlsx' 파일로 저장되었습니다.")

if __name__ == '__main__':
    main() 