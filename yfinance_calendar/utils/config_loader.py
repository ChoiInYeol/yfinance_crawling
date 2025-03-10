"""
Yahoo Finance 캘린더 크롤러의 설정을 로드하는 유틸리티
"""

import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """설정 로더 클래스
    
    YAML 파일에서 XPath 선택자와 기타 설정을 로드합니다.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        설정 로더 초기화
        
        Args:
            config_dir (Optional[str]): 설정 파일이 있는 디렉토리 경로.
                                      기본값은 현재 파일의 상위 디렉토리의 config 폴더
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.config_dir = config_dir
        self.selectors = self._load_selectors()
        self.class_selectors = self._load_class_selectors()
    
    def _load_selectors(self) -> Dict[str, Any]:
        """
        XPath 선택자 설정을 로드
        
        Returns:
            Dict[str, Any]: 로드된 선택자 설정
        """
        selector_path = os.path.join(self.config_dir, 'selectors.yaml')
        try:
            with open(selector_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"선택자 설정 로드 실패: {str(e)}")
    
    def _load_class_selectors(self) -> Dict[str, Any]:
        """
        CSS 클래스 선택자 설정을 로드
        
        Returns:
            Dict[str, Any]: 로드된 클래스 선택자 설정
        """
        selector_path = os.path.join(self.config_dir, 'class_selectors.yaml')
        try:
            with open(selector_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"클래스 선택자 설정 로드 실패: {str(e)}")
    
    def get_selector(self, calendar_type: str, selector_path: str) -> str:
        """
        특정 캘린더 타입의 선택자를 가져옴
        
        Args:
            calendar_type (str): 캘린더 타입 (earnings, economic, ipo, splits)
            selector_path (str): 선택자 경로 (예: 'columns.symbol.value')
        
        Returns:
            str: XPath 선택자
        """
        try:
            # 경로를 점으로 분리하여 딕셔너리 탐색
            parts = selector_path.split('.')
            current = self.selectors[calendar_type]
            for part in parts:
                current = current[part]
            return current
        except KeyError:
            raise KeyError(f"선택자를 찾을 수 없음: {calendar_type}.{selector_path}")
    
    def get_common_selector(self, selector_path: str) -> str:
        """
        공통 선택자를 가져옴
        
        Args:
            selector_path (str): 선택자 경로 (예: 'pagination.results_count')
        
        Returns:
            str: XPath 선택자
        """
        try:
            # 경로를 점으로 분리하여 딕셔너리 탐색
            parts = selector_path.split('.')
            current = self.selectors['common']
            for part in parts:
                current = current[part]
            return current
        except KeyError:
            raise KeyError(f"공통 선택자를 찾을 수 없음: {selector_path}")
    
    def get_class_selector(self, calendar_type: str, selector_path: str) -> str:
        """
        특정 캘린더 타입의 CSS 클래스 선택자를 가져옴
        
        Args:
            calendar_type (str): 캘린더 타입 (earnings, economic, ipo, splits)
            selector_path (str): 선택자 경로 (예: 'cells.symbol')
        
        Returns:
            str: CSS 클래스 선택자
        """
        try:
            # 경로를 점으로 분리하여 딕셔너리 탐색
            parts = selector_path.split('.')
            current = self.class_selectors[calendar_type]
            for part in parts:
                current = current[part]
            return current
        except KeyError:
            raise KeyError(f"클래스 선택자를 찾을 수 없음: {calendar_type}.{selector_path}")
    
    def get_common_class_selector(self, selector_path: str) -> str:
        """
        공통 CSS 클래스 선택자를 가져옴
        
        Args:
            selector_path (str): 선택자 경로 (예: 'pagination.results_text')
        
        Returns:
            str: CSS 클래스 선택자
        """
        try:
            # 경로를 점으로 분리하여 딕셔너리 탐색
            parts = selector_path.split('.')
            current = self.class_selectors['common']
            for part in parts:
                current = current[part]
            return current
        except KeyError:
            raise KeyError(f"공통 클래스 선택자를 찾을 수 없음: {selector_path}")
    
    def get_column_selectors(self, calendar_type: str) -> Dict[str, Dict[str, str]]:
        """
        특정 캘린더 타입의 모든 컬럼 선택자를 가져옴
        
        Args:
            calendar_type (str): 캘린더 타입 (earnings, economic, ipo, splits)
        
        Returns:
            Dict[str, Dict[str, str]]: 컬럼별 선택자 정보
        """
        try:
            return self.selectors[calendar_type]['columns']
        except KeyError:
            raise KeyError(f"캘린더 타입의 컬럼 선택자를 찾을 수 없음: {calendar_type}") 