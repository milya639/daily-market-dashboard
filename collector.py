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
    한국은행 Open API (ECOS)를 통해 원/달러 환율(매매기준율) 가져오기
    통계표코드: 036Y001 (시장평균환율(매매기준율) 등)
    주기: DD (일일)
    검색항목코드: 0000001 (원/달러)
    """
    api_key = os.environ.get("BOK_API_KEY")
    if not api_key:
        print("Error: BOK_API_KEY not found.")
        return None

    # [중요] '오늘' 데이터가 아직 집계되지 않았거나(아침 일찍), 주말인 경우를 대비해
    # 조회 기간을 '7일 전 ~ 오늘'로 설정하고 그중 가장 마지막(최신) 값을 가져옵니다.
    today = datetime.now()
    end_date = today.strftime("%Y%m%d")                  # 오늘
    start_date = (today - timedelta(days=7)).strftime("%Y%m%d")  # 7일 전
    
    # 요청하신 URL 포맷 적용
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/036Y001/DD/{start_date}/{end_date}/0000001"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 데이터가 정상적으로 들어왔는지 확인
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            # row 리스트의 가장 마지막 요소(-1)가 가장 최근 데이터입니다.
            last_item = data['StatisticSearch']['row'][-1]
            price = last_item['DATA_VALUE']
            print(f"BOK Exchange Rate Date: {last_item['TIME']}") # 로그 확인용
            return float(price)
        else:
            print("BOK API Error: No data found or API structure changed.")
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
