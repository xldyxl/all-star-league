import requests
import pandas as pd
from urllib.parse import quote

# ==========================================
# 설정 정보
# ==========================================
API_KEY = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"
NICKNAME = "Special블루"  

HEADERS = {
    "x-nxopen-api-key": API_KEY
}

def get_spid_metadata():
    print("➡ 선수 이름 데이터베이스 로딩 중...")
    url = "https://open.api.nexon.com/static/fconline/meta/spid.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {item['id']: item['name'] for item in response.json()}
    except Exception:
        pass
    return {}

def get_ouid(nickname):
    encoded_nickname = quote(nickname)
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={encoded_nickname}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("ouid")
    except Exception:
        pass
    return None

def get_recent_trades(ouid, trade_type, limit=50):
    # 💡 offset=0을 사용하여 가장 최신 데이터부터 limit 개수만큼만 정확히 가져옵니다.
    url = f"https://open.api.nexon.com/fconline/v1/user/trade?ouid={ouid}&tradetype={trade_type}&offset=0&limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠ {trade_type} 통신 오류: {e}")
    return []

if __name__ == "__main__":
    print(f"[{NICKNAME}] 유저의 최신 거래 내역 50건을 조회합니다...")
    
    spid_map = get_spid_metadata()
    user_ouid = get_ouid(NICKNAME)
    
    if user_ouid:
        # 구매 최근 50건, 판매 최근 50건 조회
        buy_data = get_recent_trades(user_ouid, "buy", limit=50)
        for item in buy_data:
            item['거래구분'] = '구매'
            
        sell_data = get_recent_trades(user_ouid, "sell", limit=50)
        for item in sell_data:
            item['거래구분'] = '판매'
            
        all_data = buy_data + sell_data
        
        if not all_data:
            print("\n📭 조회된 거래 내역이 없습니다.")
        else:
            df = pd.DataFrame(all_data)
            
            if 'spid' in df.columns:
                df['선수이름'] = df['spid'].map(lambda x: spid_map.get(x, f"알수없음({x})"))
                
            if 'tradeDate' in df.columns:
                df['tradeDate'] = pd.to_datetime(df['tradeDate'])
                # 💡 구매와 판매를 합친 후, 가장 최신순으로 정렬하고 딱 50개만 자릅니다.
                df = df.sort_values(by='tradeDate', ascending=False).head(50)
                df['tradeDate'] = df['tradeDate'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
            df = df.rename(columns={
                'tradeDate': '거래일시',
                'grade': '강화등급',
                'value': '거래금액(BP)'
            })
            
            columns_order = ['거래일시', '거래구분', '선수이름', '강화등급', '거래금액(BP)']
            final_columns = [col for col in columns_order if col in df.columns]
            df = df[final_columns]

            file_name = f"{NICKNAME}_FC온라인_최근50건_거래내역.xlsx"
            df.to_excel(file_name, index=False)
            print(f"\n✅ [성공] 현시점 기준 가장 최근 거래 내역 {len(df)}건이 저장되었습니다!")
            print(f"📁 생성된 파일명: {file_name}")
    else:
        print("❌ 유저 식별자(OUID)를 찾지 못했습니다.")