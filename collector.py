import os
import json
import requests
from datetime import datetime, timedelta, timezone

# 데이터 저장 파일명
DATA_FILE = "data.json"

def get_fred_yield():
    """
    FRED API에서 미국채 30년물 금리 가져오기 (Series ID: DGS30)
    """
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    
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

    # 한국 시간 기준 '오늘'을 구하기 위해 UTC+9 적용
    kst_timezone = timezone(timedelta(hours=9))
    today = datetime.now(timezone.utc).astimezone(kst_timezone)
    
    end_date = today.strftime("%Y%m%d")
    start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
    
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10/731Y001/D/{start_date}/{end_date}/0000001"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
            rows = data['StatisticSearch']['row']
            last_item = rows[-1]
            price = last_item['DATA_VALUE']
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

    # 2. 한국 시간(KST) 구하기
    # UTC 현재 시간을 가져온 뒤 9시간을 더한 타임존으로 변환
    kst_timezone = timezone(timedelta(hours=9))
    now_kst = datetime.now(timezone.utc).astimezone(kst_timezone)
    
    # 예: "2026-01-07 09:33 (KST)"
    updated_at_str = now_kst.strftime("%Y-%m-%d %H:%M") + " (KST)"

    # 3. JSON 구조 생성
    data = {
        "updated_at": updated_at_str,
        "us_30y": us_30y if us_30y else 0.0,
        "usd_krw": usd_krw if usd_krw else 0.0
    }

    # 4. 파일 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    
    print(f"Data saved: {data}")

if __name__ == "__main__":
    main()
