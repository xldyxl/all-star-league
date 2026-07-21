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
    "Special블루",
    "콩콩콩룔",
    "Voor",
    "익덕",
    "검정소",
    "방덕",
    "UNIT",
    "Gucci차붐",
    "kingdom21",
    "왕두",
    "앙쿠",
    "Gucci와퍼",
    "비주류중독",
    "경남FC가즈아",
    "스페인에서왔어용",
    "은안"
]

TARGET_START_DATETIME = "2026-07-19T13:49:59"

# ✅ 2개의 출력 파일을 위한 저장 경로 및 파일명 설정
SAVE_DIR = r"C:\Users\원영이\Desktop\ATL AUTO"
GOAL_FILENAME = "API데이터 경기 및 득점 검수.csv"
ASSIST_FILENAME = "API원본 어시스트 기록.csv"

GOAL_SAVE_PATH = os.path.join(SAVE_DIR, GOAL_FILENAME)
ASSIST_SAVE_PATH = os.path.join(SAVE_DIR, ASSIST_FILENAME)

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
# 3. 리그 매치 상세 분석 (득점 & 도움 동시 추출)
# ------------------------------------------
print(f"\n🚀 총 {len(all_league_matches)}개의 경기 중 리그 내전 선별 및 데이터 동시 추출 시작...")

goal_results = []    # 득점 기록 저장용 리스트
assist_results = []  # 도움 기록 저장용 리스트

for i, m_id in enumerate(all_league_matches):
    if (i + 1) % 50 == 0:
        print(f"... {i + 1}개 경기 상세 조회 완료 ...")
        
    time.sleep(0.1) # 서버 차단 방지용 안전장치
    
    # ✅ 알잘딱깔센: 429 제한 걸렸을 때 데이터가 누락되지 않도록 재시도 로직 적용
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
        
        scorers = []
        assisters = []
        
        # ✅ 단 한 번의 반복문에서 득점과 도움 데이터를 동시에 추출
        for team in m_infos:
            t_name = p1_name if team.get('ouid') == ouid1 else p2_name
            for p in team.get('player', []):
                status = p.get('status', {})
                goal_count = status.get('goal', 0)
                assist_count = status.get('assist', 0)
                
                if goal_count > 0:
                    scorers.append(f"{t_name}_{p.get('spId')}({goal_count}골)")
                if assist_count > 0:
                    assisters.append(f"{t_name}_{p.get('spId')}({assist_count}도움)")

        # 경기 공통 기본 정보
        base_info = {
            '일시': m_datetime_pretty,
            '홈': p1_name,
            '어웨이': p2_name,
            '스코어': f"{score1}_{score2}",
            '홈결과': result1
        }
        
        # 1) 득점 행 추가
        goal_row = base_info.copy()
        goal_row['득점명단'] = ", ".join(scorers)
        goal_results.append(goal_row)
        
        # 2) 어시스트 행 추가
        assist_row = base_info.copy()
        assist_row['도움명단'] = ", ".join(assisters)
        assist_results.append(assist_row)

# ------------------------------------------
# 4. 2개의 DataFrame 생성, 정렬 및 각각 저장
# ------------------------------------------
# ✅ 바탕화면 폴더가 없을 경우 자동 생성
os.makedirs(SAVE_DIR, exist_ok=True)

# 1) 득점 파일 저장
df_goal = pd.DataFrame(goal_results)
if not df_goal.empty:
    df_goal = df_goal.sort_values(by='일시', ascending=False)
df_goal.to_csv(GOAL_SAVE_PATH, index=False, encoding="utf-8-sig")

# 2) 어시스트 파일 저장
df_assist = pd.DataFrame(assist_results)
if not df_assist.empty:
    df_assist = df_assist.sort_values(by='일시', ascending=False)
df_assist.to_csv(ASSIST_SAVE_PATH, index=False, encoding="utf-8-sig")

print(f"\n🎉 모든 데이터 추출 및 저장 완료! (기준: {TARGET_START_DATETIME} 이후)")
print(f"📍 [득점 파일] 저장 완료: {GOAL_SAVE_PATH}")
print(f"📍 [도움 파일] 저장 완료: {ASSIST_SAVE_PATH}")