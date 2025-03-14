import requests
import logging
import zipfile
import io
import xml.etree.ElementTree as ET

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bridge")

class DartAPI:
    """DART OpenAPI와 상호작용하는 클래스"""
    
    def __init__(self, api_key):
        """DART API 클래스 초기화
        
        Args:
            api_key (str): DART OpenAPI 키
        """
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
    
    def get_corp_codes(self):
        """기업 코드 목록 조회
        
        Returns:
            list: 기업 코드, 이름, 주식 코드 정보 목록
        """
        url = f"{self.base_url}/corpCode.xml"
        params = {
            "crtfc_key": self.api_key
        }
        
        if not self.api_key:
            logger.error("API 키가 없습니다.")
            return None
        
        try:
            logger.info("기업 코드 목록 조회 API 호출")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"API 호출 에러: {response.status_code}")
                return None
            
            # zip 파일을 메모리에서 처리
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                xml_data = zip_file.read(zip_file.namelist()[0])
            
            # XML 파싱
            root = ET.fromstring(xml_data)
            corp_list = []
            
            for company in root.findall('list'):
                corp_code = company.findtext('corp_code')
                corp_name = company.findtext('corp_name')
                stock_code = company.findtext('stock_code')
                modify_date = company.findtext('modify_date')
                
                if stock_code and stock_code.strip():  # 상장 기업만 필터링
                    corp_list.append({
                        'corp_code': corp_code,
                        'corp_name': corp_name,
                        'stock_code': stock_code,
                        'modify_date': modify_date
                    })
            
            logger.info(f"총 {len(corp_list)}개의 기업 코드를 검색했습니다.")
            return corp_list
        except Exception as e:
            logger.error(f"기업 코드 조회 오류: {str(e)}")
            return None
    
    def get_company_info(self, corp_code):
        """기업 기본 정보 조회
        
        Args:
            corp_code (str): 기업 고유 코드
            
        Returns:
            dict: 기업 기본 정보
        """
        url = f"{self.base_url}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }
        
        try:
            logger.info(f"기업 정보 API 호출: {corp_code}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"기업 정보 조회 에러: {response.status_code}")
                return None
            
            data = response.json()
            if data.get('status') != '000':
                logger.error(f"기업 정보 API 오류: {data.get('message')}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"기업 정보 조회 오류: {str(e)}")
            return None
    
    def get_financial_statements(self, corp_code, bsns_year, reprt_code="11011"):
        """사업보고서 재무제표 정보 조회
        
        Args:
            corp_code (str): 기업 고유 코드
            bsns_year (str): 사업연도
            reprt_code (str, optional): 보고서 코드. 기본값은 "11011" (사업보고서)
            
        Returns:
            dict: 재무제표 정보
        """
        url = f"{self.base_url}/fnlttSinglAcntAll.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": "CFS"  # 연결재무제표
        }
        
        try:
            logger.info(f"재무제표 API 호출: {corp_code} {bsns_year}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"재무제표 조회 에러: {response.status_code}")
                return None
            
            data = response.json()
            if data.get('status') != '000':
                logger.error(f"재무제표 API 오류: {data.get('message')}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"재무제표 조회 오류: {str(e)}")
            return None