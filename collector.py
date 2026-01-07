import os
import json
import requests
from datetime import datetime, timedelta

# 데이터 저장 파일명
DATA_FILE = "data.json"

def get_fred_yield():
    """
    FRED API에서 미국채 30년물 금리 가져오기 (Series ID: DGS30)
    """
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    
    # 최신 1건만 조회
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS30&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        val = data['observations'][0]['value']
        return float(val) if val != "." else None
    except Exception as e:
        print(f"FRED Error: {e}")
        return None

def get_usd_krw():
    """
    한국은행 Open API (ECOS)를 통해 원/달러 환율 가져오기
    통계표코드: 731Y001 (주요국 통화의 대원화환율)
    주기: D (일일)
    항목코드: 0000001 (원/미국달러)
    """
    api_key = os.environ.get("BOK_API_KEY")
    if not api_key:
        print("Error: BOK_API_KEY not found.")
        return None

    # [날짜 로직]
    # 오늘이 주말이거나 공휴일, 혹은 아직 장 마감 전일 수 있으므로
    # '오늘'만 조회하면 데이터가 없을 수 있습니다.
    # 따라서 '7일 전'부터 '오늘'까지를 조회한 뒤 가장 마지막(최신) 값을 씁니다.
    today = datetime.now()
    end_date = today.strftime("%Y%m%d")                  # 오늘
    start_date = (today - timedelta(days=7)).strftime("%Y%m%d")  # 7일 전
    
    # https://getidiom.com/dictionary/korean/%EA%B5%AC%EC%84%B1
    # 사용자가 제공한 731Y001 코드 적용.
    # 파싱 편의를 위해 /xml/ 대신 /json/을 사용합니다.
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10/731Y001/D/{start_date}/{end_date}/0000001"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 응답 구조 확인 및 데이터 추출
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            rows = data['StatisticSearch']['row']
            # 기간 내 데이터 중 가장 마지막(최신) 항목 선택
            last_item = rows[-1] 
            
            price = last_item['DATA_VALUE']
            date = last_item['TIME']
            
            print(f"BOK Exchange Rate Date: {date}, Value: {price}") # 로그 확인용
            
            # 쉼표(,)가 포함된 문자열일 수 있으므로 제거 후 float 변환
            return float(price.replace(",", ""))
        else:
            print("BOK API Error: No data found in range.")
            return None
            
    except Exception as e:
        print(f"BOK Error: {e}")
        return None

def main():
    # 1. 데이터 수집
    us_30y = get_fred_yield()
    usd_krw = get_usd_krw()

    # 2. JSON 구조 생성
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "us_30y": us_30y if us_30y else 0.0,
        "usd_krw": usd_krw if usd_krw else 0.0
    }

    # 3. 파일 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    
    print(f"Data saved: {data}")

if __name__ == "__main__":
    main()
