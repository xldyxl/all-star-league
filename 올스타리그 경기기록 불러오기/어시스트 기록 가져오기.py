import requests
import pandas as pd
import time
import os  # ✅ 알잘딱깔센: 경로 설정을 위해 os 모듈 추가

# ==========================================
# 1. 설정
# ==========================================
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1bf0d4ed1c4a60f2b2f071f78b4e3b165efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

league_players = [
    "UNIT", "검정소", "ZD장인지참치",
    "아들러", "유표", "Voor",
    "0708ManUtd", "Special블루", "은안",
    "ZD장인흥미니7", "Angel코레아", "Gucci박장군",
    "FT난테", "강해린의무회전킥", "kingdom21", "Gucci와퍼",
    "콩콩콩룔"
]

# 기준 일시
TARGET_START_DATETIME = "2026-05-27T10:59:01"

# ✅ 요청하신 저장 경로 및 파일명 설정
SAVE_DIR = r"C:\Users\원영이\Desktop\ATL AUTO"
SAVE_FILENAME = "API원본 어시스트 기록.csv"
FULL_SAVE_PATH = os.path.join(SAVE_DIR, SAVE_FILENAME)

def get_ouid(nickname):
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}"
    res = requests.get(url, headers=headers)
    return res.json().get('ouid') if res.status_code == 200 else None

# ------------------------------------------
# 1. 리그 참가자의 OUID 매핑
# ------------------------------------------
print("🔍 리그 참가자들의 OUID 정보 확인 중...")
player_map = {}
for p in league_players:
    ouid = get_ouid(p)
    if ouid:
        player_map[p] = ouid
    time.sleep(0.1)

league_ouids = set(player_map.values())
all_league_matches = set()
match_results = []

print(f"\n✅ 확인된 참가자: {len(player_map)}명. 경기 기록 수집 시작...")

# ------------------------------------------
# 2. 각 유저별 경기 ID 수집
# ------------------------------------------
for name, ouid in player_map.items():
    print(f"📊 {name}님의 최근 '클래식 1on1(40)' 기록 조회 중...")
    offset = 0
    while offset < 500: 
        res = requests.get(f"https://open.api.nexon.com/fconline/v1/user/match?ouid={ouid}&matchtype=40&offset={offset}&limit=100", headers=headers)
        if res.status_code != 200: break
        match_ids = res.json()
        if not match_ids: break
        all_league_matches.update(match_ids)
        offset += 100
        time.sleep(0.05)

# ------------------------------------------
# 3. 리그 매치 상세 분석
# ------------------------------------------
print(f"\n🚀 총 {len(all_league_matches)}개의 경기 중 리그 내전 선별 및 데이터 추출 시작...")

for i, m_id in enumerate(all_league_matches):
    if (i + 1) % 50 == 0:
        print(f"... {i + 1}개 경기 상세 조회 완료 ...")
        
    time.sleep(0.1) # 서버 차단 방지용 안전장치
    
    # 429 제한 걸렸을 때 데이터가 누락되지 않도록 재시도하는 루프
    while True:
        d_res = requests.get(f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={m_id}", headers=headers)
        if d_res.status_code == 429:
            print("⏳ API 요청 한도 도달! 5초간 휴식 후 이 경기를 재시도합니다...")
            time.sleep(5)
            continue  
        break  
        
    if d_res.status_code != 200: 
        continue
    
    data = d_res.json()
    m_date_raw = data.get('matchDate', '') 
    
    # 기준 시간 이전 경기 필터링
    if m_date_raw < TARGET_START_DATETIME: continue
    
    m_datetime_pretty = m_date_raw.replace('T', ' ')
    m_infos = data.get('matchInfo', [])
    if len(m_infos) != 2: continue
    
    ouid1, ouid2 = m_infos[0].get('ouid'), m_infos[1].get('ouid')
    
    # 내전 여부 확인
    if ouid1 in league_ouids and ouid2 in league_ouids:
        p1_name = next(k for k, v in player_map.items() if v == ouid1)
        p2_name = next(k for k, v in player_map.items() if v == ouid2)
        
        score1 = m_infos[0].get('shoot', {}).get('goalTotal', 0)
        score2 = m_infos[1].get('shoot', {}).get('goalTotal', 0)
        result1 = m_infos[0].get('matchDetail', {}).get('matchResult')
        
        # 도움(어시스트) 기록 선수 추출
        assisters = []
        for team in m_infos:
            t_name = p1_name if team.get('ouid') == ouid1 else p2_name
            for p in team.get('player', []):
                assist_count = p.get('status', {}).get('assist', 0)
                if assist_count > 0:
                    assisters.append(f"{t_name}_{p.get('spId')}({assist_count}도움)")

        match_results.append({
            '일시': m_datetime_pretty,
            '홈': p1_name,
            '어웨이': p2_name,
            '스코어': f"{score1}:{score2}",
            '홈결과': result1,
            '도움명단': ", ".join(assisters)
        })

# ------------------------------------------
# 4. 저장 및 정렬
# ------------------------------------------
df = pd.DataFrame(match_results)
if not df.empty:
    df = df.sort_values(by='일시', ascending=False)

# ✅ 폴더가 없을 경우를 대비해 폴더 자동 생성 기능 추가
os.makedirs(SAVE_DIR, exist_ok=True)
    
# ✅ 지정된 경로 및 파일명으로 최종 저장
df.to_csv(FULL_SAVE_PATH, index=False, encoding="utf-8-sig")
print(f"\n🎉 검증 데이터 저장 완료!")
print(f"📍 저장 위치: {FULL_SAVE_PATH}")