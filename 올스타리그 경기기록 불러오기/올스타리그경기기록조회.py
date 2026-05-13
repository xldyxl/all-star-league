import requests
import pandas as pd
import time

# 1. 설정
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

league_players = [
    "Voor", "UNIT", "아들러", "ZD장인지참치", "검정소", 
    "Angel코레아", "0708ManUtd", "chilishake", "Special블루", "Gucci박장군", 
    "ZD장인흥미니7", "조바리안", "kingdom21", "오스트리아", "은안", "Eve올로"
]

# 💡 수정된 부분: 2026년 4월 25일 오전 3시 정각
TARGET_START_DATETIME = "2026-05-11T13:44:00"

def get_ouid(nickname):
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}"
    res = requests.get(url, headers=headers)
    return res.json().get('ouid') if res.status_code == 200 else None

# 1. 16명의 OUID 매핑
print("🔍 리그 참가자 16명의 OUID 정보 확인 중...")
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

# 2. 각 유저별 경기 ID 수집
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

# 3. 리그 매치 상세 분석
print(f"\n🚀 총 {len(all_league_matches)}개의 경기 중 리그 내전 선별 및 데이터 추출 시작...")

for i, m_id in enumerate(all_league_matches):
    if (i + 1) % 50 == 0:
        print(f"... {i + 1}개 경기 상세 조회 완료 ...")
        
    time.sleep(0.1) # 서버 차단 방지용 안전장치
    
    d_res = requests.get(f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={m_id}", headers=headers)
    
    if d_res.status_code == 429:
        print("⏳ API 요청 한도 도달! 5초간 휴식합니다...")
        time.sleep(5)
        continue
    elif d_res.status_code != 200: 
        continue
    
    data = d_res.json()
    m_date_raw = data.get('matchDate', '') 
    
    # 💡 여기서 4월 26일 새벽 3시 이전 경기들을 걸러냅니다.
    if m_date_raw < TARGET_START_DATETIME: continue
    
    m_datetime_pretty = m_date_raw.replace('T', ' ')
    m_infos = data.get('matchInfo', [])
    if len(m_infos) != 2: continue
    
    ouid1, ouid2 = m_infos[0].get('ouid'), m_infos[1].get('ouid')
    
    if ouid1 in league_ouids and ouid2 in league_ouids:
        p1_name = next(k for k, v in player_map.items() if v == ouid1)
        p2_name = next(k for k, v in player_map.items() if v == ouid2)
        
        score1 = m_infos[0].get('shoot', {}).get('goalTotal', 0)
        score2 = m_infos[1].get('shoot', {}).get('goalTotal', 0)
        result1 = m_infos[0].get('matchDetail', {}).get('matchResult')
        
        scorers = []
        for team in m_infos:
            t_name = p1_name if team.get('ouid') == ouid1 else p2_name
            for p in team.get('player', []):
                goal_count = p.get('status', {}).get('goal', 0)
                if goal_count > 0:
                    scorers.append(f"{t_name}_{p.get('spId')}({goal_count}골)")

        match_results.append({
            '일시': m_datetime_pretty,
            '홈': p1_name,
            '어웨이': p2_name,
            '스코어': f"{score1}:{score2}",
            '홈결과': result1,
            '득점명단': ", ".join(scorers)
        })

# 4. 저장 및 정렬
df = pd.DataFrame(match_results)
if not df.empty:
    df = df.sort_values(by='일시', ascending=False)
    
df.to_csv("AllStar_League_Match_Verify_Latest.csv", index=False, encoding="utf-8-sig")
print(f"\n🎉 검증 데이터 저장 완료! (기준: {TARGET_START_DATETIME} 이후)")