import requests
import pandas as pd
from urllib.parse import quote  # 한글 닉네임 인코딩을 위한 모듈

# ==========================================
# 설정 정보
# ==========================================
# 발급받은 LIVE API 키
API_KEY = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"

# 여기에 본인의 실제 게임 내 닉네임을 정확히 입력하세요.
NICKNAME = "UNIT"  

HEADERS = {
    "x-nxopen-api-key": API_KEY
}

def get_ouid(nickname):
    """닉네임으로 유저 고유 식별자(OUID) 조회 (URL 인코딩 적용)"""
    # 한글 닉네임을 안전하게 URL로 전달하기 위해 인코딩 처리
    encoded_nickname = quote(nickname)
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={encoded_nickname}"
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("ouid")
    else:
        print(f"❌ OUID 조회 실패 (코드: {response.status_code}): {response.text}")
        return None

def get_trade_history(ouid, trade_type="buy"):
    """거래 내역 조회 (buy: 구매, sell: 판매)"""
    url = f"https://open.api.nexon.com/fconline/v1/user/trade?ouid={ouid}&tradetype={trade_type}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 거래 내역 조회 실패 (코드: {response.status_code}): {response.text}")
        return []

def save_to_excel(data, nickname):
    """데이터를 판다스 데이터프레임으로 변환 후 엑셀 저장"""
    if not data:
        print("📭 조회된 거래 내역이 없습니다. (최근 거래가 없거나 반영 전일 수 있습니다)")
        return

    # API 응답 데이터를 데이터프레임으로 변환
    df = pd.DataFrame(data)
    
    # 날짜 가독성 개선 (ISO 8601 -> 년-월-일 시:분:초)
    if 'tradeDate' in df.columns:
        df['tradeDate'] = pd.to_datetime(df['tradeDate']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 파일명 설정 및 저장
    file_name = f"{nickname}_FC온라인_구매내역.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n✅ [성공] 이적시장 내역이 엑셀로 저장되었습니다.")
    print(f"📁 파일명: {file_name}")

# ==========================================
# 실행 메인 루틴
# ==========================================
if __name__ == "__main__":
    print(f"[{NICKNAME}] 유저의 데이터를 불러오는 중...")
    
    # 1. OUID 조회
    user_ouid = get_ouid(NICKNAME)
    
    if user_ouid:
        print("✅ OUID 조회 성공!")
        # 2. 구매 내역(buy) 가져오기
        print("이적시장 구매 내역을 요청합니다...")
        buy_data = get_trade_history(user_ouid, "buy")
        
        # 3. 엑셀 파일 저장
        save_to_excel(buy_data, NICKNAME)