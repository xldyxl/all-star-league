import requests
import pandas as pd
import time
import os

# ==========================================
# 1. 사용자 설정 영역
# ==========================================
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1bf0d4ed1c4a60f2b2f071f78b4e3b165efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

# ✅ 1) 조회할 유저 닉네임
TARGET_NICKNAME = "인강전사"

# ✅ 2) 조회 기간 설정 (YYYY-MM-DD 형식) - 1월 1일부터 설정!
START_DATE = "2026-01-01"
END_DATE = "2026-07-21"

# 상세 시간 기준 (문자열 비교용)
START_DATETIME = f"{START_DATE}T00:00:00"
END_DATETIME = f"{END_DATE}T23:59:59"

# ✅ 3) 저장 파일 경로
SAVE_DIR = r"C:\Users\원영이\Desktop\ATL AUTO"
SAVE_FILENAME = f"클래식1on1기록_{TARGET_NICKNAME}_{START_DATE}_{END_DATE}.csv"
SAVE_PATH = os.path.join(SAVE_DIR, SAVE_FILENAME)

# ==========================================
# 2. OUID <-> 닉네임 조회 함수
# ==========================================
def get_ouid(nickname):
    url = f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}"
    res = requests.get(url, headers=headers)
    return res.json().get('ouid') if res.status_code == 200 else None

def get_nickname_by_ouid(ouid):
    url = f"https://open.api.nexon.com/fconline/v1/user/basic?ouid={ouid}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get('nickname', '알수없는유저')
    return '알수없는유저'

print(f"🔍 '{TARGET_NICKNAME}' 님의 OUID 조회 중...")
target_ouid = get_ouid(TARGET_NICKNAME)

if not target_ouid:
    print("❌ 유저를 찾을 수 없습니다. 닉네임을 확인해주세요!")
    exit()
print(f"✅ OUID 확인 완료: {target_ouid}\n")

# ==========================================
# 3. [한도 해제!] 1월 1일까지 매치 ID 무제한 수집
# ==========================================
print(f"📊 '{TARGET_NICKNAME}' 님의 '클래식 1on1(40)' 경기 ID 목록 수집 중 (한도 해제 모드)...")

match_ids = []
offset = 0

while True:
    res = requests.get(
        f"https://open.api.nexon.com/fconline/v1/user/match?ouid={target_ouid}&matchtype=40&offset={offset}&limit=100", 
        headers=headers
    )
    
    if res.status_code != 200 or not res.json():
        print(" └ 더 이상 조회되는 경기 ID가 없습니다.")
        break
        
    fetched_ids = res.json()
    match_ids.extend(fetched_ids)
    
    print(f"... 현재 {len(match_ids)}개 매치 ID 확보 중 (offset={offset}) ...")
    offset += 100
    time.sleep(0.08)  # API 과부하 방지

print(f"\n✅ 총 {len(match_ids)}개의 경기 ID를 확보했습니다. {START_DATE} ~ {END_DATE} 기간 데이터 추출을 시작합니다...\n")

# ==========================================
# 4. 매치 상세 조회 및 기간 필터링
# ==========================================
results = []
player_name_cache = {target_ouid: TARGET_NICKNAME}

for i, m_id in enumerate(match_ids):
    time.sleep(0.1)  # 6개월치 대량 조회를 위한 쿨타임
    
    while True:
        d_res = requests.get(f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={m_id}", headers=headers)
        if d_res.status_code == 429:
            print("⏳ API 요청 한도 도달! 5초간 휴식 후 재시도합니다...")
            time.sleep(5)
            continue
        break
        
    if d_res.status_code != 200:
        continue
        
    data = d_res.json()
    m_date_raw = data.get('matchDate', '')
    
    # 📌 [핵심!] 설정한 1월 1일보다 과거 경기가 나오면 그 즉시 크롤링 완벽 종료
    if m_date_raw < START_DATETIME:
        print(f"\n⏹️ 설정한 시작일({START_DATE}) 이전 경기에 도달하여 조회를 성공적으로 완료했습니다!")
        break
        
    # 종료일 이후의 미래 경기는 스킵
    if m_date_raw > END_DATETIME:
        continue

    m_infos = data.get('matchInfo', [])
    if len(m_infos) != 2:
        continue
        
    my_info = m_infos[0] if m_infos[0].get('ouid') == target_ouid else m_infos[1]
    opp_info = m_infos[1] if m_infos[0].get('ouid') == target_ouid else m_infos[0]
    
    # 상대방 감독명 조회 및 캐싱
    opp_ouid = opp_info.get('ouid')
    if opp_ouid not in player_name_cache:
        opp_nick = opp_info.get('nickname')
        if not opp_nick:
            opp_nick = get_nickname_by_ouid(opp_ouid)
            time.sleep(0.05)
        player_name_cache[opp_ouid] = opp_nick
        
    opp_name = player_name_cache[opp_ouid]
    
    my_score = my_info.get('shoot', {}).get('goalTotal', 0)
    opp_score = opp_info.get('shoot', {}).get('goalTotal', 0)
    my_result = my_info.get('matchDetail', {}).get('matchResult', '무')
    
    scorers, assisters = [], []
    for p in my_info.get('player', []):
        status = p.get('status', {})
        if status.get('goal', 0) > 0:
            scorers.append(f"{p.get('spId')}({status.get('goal')}골)")
        if status.get('assist', 0) > 0:
            assisters.append(f"{p.get('spId')}({status.get('assist')}도움)")
            
    results.append({
        '일시': m_date_raw.replace('T', ' '),
        '기준유저': TARGET_NICKNAME,
        '상대유저': opp_name,
        '경기결과': my_result,
        '스코어': f"{my_score} : {opp_score}",
        '내득점수': my_score,
        '내실점수': opp_score,
        '득점명단(spId)': ", ".join(scorers),
        '도움명단(spId)': ", ".join(assisters)
    })
    
    # 진행 상황 알림 (몇 년 몇 월 경기 수집 중인지 표시)
    if len(results) % 10 == 0 and len(results) > 0:
        current_date_display = m_date_raw.split('T')[0]
        print(f"... [수집 진행 중] 총 {len(results)}건 완료 (현재 수집 날짜: {current_date_display} | 상대: {opp_name}) ...")

# ==========================================
# 5. DataFrame 저장
# ==========================================
os.makedirs(SAVE_DIR, exist_ok=True)
df = pd.DataFrame(results)

if not df.empty:
    df = df.sort_values(by='일시', ascending=False)
    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"\n🎉 총 {len(df)}건의 경기 기록 수집 완료!")
    print(f"📍 파일 저장 위치: {SAVE_PATH}")
else:
    print(f"\n⚠️ 지정한 기간({START_DATE} ~ {END_DATE}) 내에 치른 경기 기록이 없습니다.")