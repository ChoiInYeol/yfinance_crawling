"""
Yahoo Finance 캘린더 데이터를 데이터프레임으로 변환하는 유틸리티
"""

import os
import json
import glob
from typing import Dict, List, Optional
import pandas as pd


class CalendarDataLoader:
    """캘린더 데이터 로더 클래스
    
    JSON 파일에서 캘린더 데이터를 로드하여 데이터프레임으로 변환합니다.
    """
    
    def __init__(self, data_dir: str):
        """
        데이터 로더 초기화
        
        Args:
            data_dir (str): 데이터 파일이 있는 디렉토리 경로
        """
        self.data_dir = data_dir
    
    def _load_json_file(self, file_path: str) -> List[Dict]:
        """
        JSON 파일 로드
        
        Args:
            file_path (str): JSON 파일 경로
        
        Returns:
            List[Dict]: JSON 데이터
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"JSON 파일 로드 실패: {str(e)}")
    
    def load_earnings_data(self, file_pattern: str = "*_earnings.json") -> pd.DataFrame:
        """
        실적 발표 데이터 로드
        
        Args:
            file_pattern (str): 파일 패턴 (기본값: "*_earnings.json")
        
        Returns:
            pd.DataFrame: 실적 발표 데이터프레임
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        if not files:
            raise FileNotFoundError(f"실적 발표 데이터 파일을 찾을 수 없음: {file_pattern}")
        
        # 가장 최근 파일 사용
        latest_file = max(files, key=os.path.getctime)
        data = self._load_json_file(latest_file)
        
        return pd.DataFrame(data)
    
    def load_economic_data(self, file_pattern: str = "*_economic.json") -> pd.DataFrame:
        """
        경제 지표 데이터 로드
        
        Args:
            file_pattern (str): 파일 패턴 (기본값: "*_economic.json")
        
        Returns:
            pd.DataFrame: 경제 지표 데이터프레임
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        if not files:
            raise FileNotFoundError(f"경제 지표 데이터 파일을 찾을 수 없음: {file_pattern}")
        
        latest_file = max(files, key=os.path.getctime)
        data = self._load_json_file(latest_file)
        
        return pd.DataFrame(data)
    
    def load_ipo_data(self, file_pattern: str = "*_ipo.json") -> pd.DataFrame:
        """
        IPO 데이터 로드
        
        Args:
            file_pattern (str): 파일 패턴 (기본값: "*_ipo.json")
        
        Returns:
            pd.DataFrame: IPO 데이터프레임
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        if not files:
            raise FileNotFoundError(f"IPO 데이터 파일을 찾을 수 없음: {file_pattern}")
        
        latest_file = max(files, key=os.path.getctime)
        data = self._load_json_file(latest_file)
        
        return pd.DataFrame(data)
    
    def load_splits_data(self, file_pattern: str = "*_splits.json") -> pd.DataFrame:
        """
        주식 분할 데이터 로드
        
        Args:
            file_pattern (str): 파일 패턴 (기본값: "*_splits.json")
        
        Returns:
            pd.DataFrame: 주식 분할 데이터프레임
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        if not files:
            raise FileNotFoundError(f"주식 분할 데이터 파일을 찾을 수 없음: {file_pattern}")
        
        latest_file = max(files, key=os.path.getctime)
        data = self._load_json_file(latest_file)
        
        return pd.DataFrame(data)
    
    def load_all_calendar_data(self) -> Dict[str, pd.DataFrame]:
        """
        모든 캘린더 데이터 로드
        
        Returns:
            Dict[str, pd.DataFrame]: 캘린더 타입별 데이터프레임
        """
        return {
            'earnings': self.load_earnings_data(),
            'economic': self.load_economic_data(),
            'ipo': self.load_ipo_data(),
            'splits': self.load_splits_data()
        } 