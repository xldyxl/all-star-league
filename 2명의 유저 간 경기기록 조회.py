import requests
import pandas as pd
import os

# ==========================================
# 1. 환경 설정 및 API 키 입력
# ==========================================
API_KEY = "live_f4551344020f5d8e5aa2e29c8fea68b1bf0d4ed1c4a60f2b2f071f78b4e3b165efe8d04e6d233bd35cf2fabdeb93fb0d" # 🚨 발급받은 넥슨 API 키 입력
HEADERS = {"x-nxopen-api-key": API_KEY}

USER1_NICKNAME = "Special블루" # 조회할 유저 1
USER2_NICKNAME = "호야국2인" # 조회할 유저 2 (상대방)
MATCH_TYPE = 40 # 40: 클래식 1on1, 50: 공식경기 

# ==========================================
# 2. 함수 정의
# ==========================================
def get_spid_metadata():
    url = "https://open.api.nexon.com/static/fconline/meta/spid.json"
    res = requests.get(url)
    return {item['id']: item['name'] for item in res.json()}

def get_ouid(nickname):
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json().get('ouid')
    return None

def get_match_history(ouid, match_type, limit=30):
    url = f"https://open.api.nexon.com/fconline/v1/user/match?ouid={ouid}&matchtype={match_type}&offset=0&limit={limit}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def get_match_detail(match_id):
    url = f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={match_id}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return None

# ==========================================
# 3. 메인 실행 로직
# ==========================================
def main():
    print("⏳ 데이터 수집을 시작합니다...")
    
    spid_map = get_spid_metadata()
    ouid1 = get_ouid(USER1_NICKNAME)
    ouid2 = get_ouid(USER2_NICKNAME)
    
    if not ouid1 or not ouid2:
        print("❌ 유저 닉네임을 찾을 수 없습니다. 닉네임을 확인해주세요.")
        return

    match_ids = get_match_history(ouid1, MATCH_TYPE)
    target_matches = []
    
    print(f"🔍 {USER1_NICKNAME}님의 최근 {len(match_ids)}경기 중 {USER2_NICKNAME}님과의 매치를 탐색합니다...")
    for match_id in match_ids:
        match_detail = get_match_detail(match_id)
        if not match_detail or len(match_detail.get('matchInfo', [])) < 2:
            continue
            
        participants = [info['ouid'] for info in match_detail['matchInfo']]
        if ouid1 in participants and ouid2 in participants:
            target_matches.append(match_detail)
            print(f"✅ 매치 기록 발견! (매치 일시: {match_detail['matchDate']})")
            
            if len(target_matches) >= 2:
                break
            
    if not target_matches:
        print("❌ 최근 경기 기록 중에서 두 유저 간의 맞대결을 찾을 수 없습니다.")
        return

    extracted_data = []
    
    for match in target_matches:
        match_date = match['matchDate'].replace('T', ' ')
        
        for info in match['matchInfo']:
            nickname = info['nickname']
            players = info.get('player', [])
            
            for p in players:
                sp_pos = p.get('spPosition')
                status = p.get('status', {})
                sp_rating = status.get('spRating', 0.0)
                
                # 💡 [핵심 수정 부분] 미출전 교체 선수 필터링
                # 포지션이 28(SUB)이면서 평점이 0점(경기에 1초도 뛰지 않음)인 선수는 건너뜁니다.
                if sp_pos == 28 and sp_rating == 0.0:
                    continue
                
                sp_id = p.get('spId')
                player_name = spid_map.get(sp_id, f"알수없음({sp_id})")
                goals = status.get('goal', 0)
                assists = status.get('assist', 0)
                
                extracted_data.append({
                    "경기일시": match_date,
                    "유저명": nickname,
                    "출전선수이름": player_name,
                    "득점": goals,
                    "도움": assists
                })

    df = pd.DataFrame(extracted_data)
    df = df.sort_values(by=["경기일시", "유저명", "득점", "도움"], ascending=[False, True, False, False])
    
    save_path = "Match_Players_Record.xlsx"
    df.to_excel(save_path, index=False)
    print(f"\n🎉 추출 성공! 총 {len(target_matches)}경기의 출전 선수 데이터가 '{save_path}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()