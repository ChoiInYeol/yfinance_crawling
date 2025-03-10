"""
Yahoo Finance 캘린더 데이터 로드 예제
"""

import os
import sys

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from yfinance_calendar.utils.data_loader import CalendarDataLoader


def main():
    # 데이터 디렉토리 설정
    data_dir = os.path.join(project_root, 'output')
    
    # 데이터 로더 초기화
    loader = CalendarDataLoader(data_dir)
    
    try:
        # 모든 캘린더 데이터 로드
        calendar_data = loader.load_all_calendar_data()
        
        # 각 데이터프레임 출력
        for calendar_type, df in calendar_data.items():
            print(f"\n{calendar_type.upper()} 데이터:")
            print(f"행 수: {len(df)}")
            print(f"컬럼: {', '.join(df.columns)}")
            print("\n처음 5개 행:")
            print(df.head())
            print("\n" + "="*80)
        
        # 데이터프레임 활용 예시
        
        # 1. Earnings 데이터 분석
        earnings_df = calendar_data['earnings']
        if not earnings_df.empty:
            print("\n실적 발표 통계:")
            print(f"총 기업 수: {len(earnings_df['symbol'].unique())}")
            print("\nEPS 추정치가 있는 기업:")
            print(earnings_df[earnings_df['eps_estimate'].notna()][['symbol', 'company', 'eps_estimate']])
        
        # 2. Economic 데이터 분석
        economic_df = calendar_data['economic']
        if not economic_df.empty:
            print("\n경제 지표 통계:")
            print("\n국가별 이벤트 수:")
            print(economic_df['country'].value_counts().head())
            
        # 3. IPO 데이터 분석
        ipo_df = calendar_data['ipo']
        if not ipo_df.empty:
            print("\nIPO 통계:")
            print("\n거래소별 IPO 수:")
            print(ipo_df['exchange'].value_counts())
        
        # 4. Splits 데이터 분석
        splits_df = calendar_data['splits']
        if not splits_df.empty:
            print("\n주식 분할 통계:")
            print(f"총 분할 건수: {len(splits_df)}")
            print("\n옵션 가능 여부:")
            print(splits_df['optionable'].value_counts())
    
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    main() 