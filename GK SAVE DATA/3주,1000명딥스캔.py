import requests
import pandas as pd
import time

# 1. 기본 설정 (API 키 및 초기 유저 세팅)
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

nickname = "진짜왜이러세요"

# 내 OUID 가져오기
print("🔄 내 계정(OUID) 정보 불러오는 중...")
res_ouid = requests.get(f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}", headers=headers)
my_ouid = res_ouid.json().get('ouid')

# 2. ⚠️ 에러 났던 부분! 데이터 저장소 초기화
target_ouids = [my_ouid]
checked_ouids = set()
checked_matches = set()
gk_results = []

# 3. 딥 스캔 설정
TARGET_USER_COUNT = 1000
TARGET_START_DATE = "2026-03-26" # 수집 마지노선

print(f"\n--- 📅 {TARGET_START_DATE} 패치 이후 데이터 딥 스캔 시작 ---")

while len(target_ouids) > 0 and len(checked_ouids) < TARGET_USER_COUNT:
    current_ouid = target_ouids.pop(0)
    if current_ouid in checked_ouids: continue
    checked_ouids.add(current_ouid)
    
    offset = 0
    limit = 100 
    user_time_travel_done = False 
    
    while not user_time_travel_done:
        try:
            res = requests.get(f"https://open.api.nexon.com/fconline/v1/user/match?ouid={current_ouid}&matchtype=50&offset={offset}&limit={limit}", headers=headers)
            
            # API 제한 걸리면 5초 대기 후 다시 시도
            if res.status_code == 429:
                time.sleep(5)
                continue
                
            match_ids = res.json()
            if not match_ids: 
                break 
                
            for m_id in match_ids:
                if m_id in checked_matches: continue
                checked_matches.add(m_id)
                
                d_res = requests.get(f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={m_id}", headers=headers)
                if d_res.status_code != 200: continue
                
                data = d_res.json()
                m_date = data.get('matchDate', '').split('T')[0]
                
                # 🛑 타임머신 종료: 3/26 이전 경기면 즉시 탈출
                if m_date < TARGET_START_DATE:
                    user_time_travel_done = True
                    break 
                
                m_infos = data.get('matchInfo', [])
                if len(m_infos) != 2: continue
                
                for i, team in enumerate(m_infos):
                    opp = m_infos[1] if i == 0 else m_infos[0]
                    # 거미줄 확장
                    if team.get('ouid') not in checked_ouids: target_ouids.append(team.get('ouid'))
                    
                    eff = opp.get('shoot', {}).get('effectiveShootTotal', 0)
                    goal = opp.get('shoot', {}).get('goalTotal', 0)
                    gk_id = next((p.get('spId') for p in team.get('player', []) if p.get('spPosition') == 0), None)
                    
                    if gk_id:
                        gk_results.append({'날짜': m_date, 'GK_ID': gk_id, '피슈팅': eff, '선방': max(0, eff-goal)})

            # 아직 3/26 도달 못했으면 다음 100경기 더 탐색
            offset += 100 
            if offset > 500: # 500경기 제한 안전장치
                break
                
        except Exception as e:
            break 

    # 유저 10명마다 백업 및 로그 출력
    if len(checked_ouids) % 10 == 0:
        print(f"📊 {len(checked_ouids)}명 분석 완료... 누적 데이터 {len(gk_results)}건 (과거 기록 딥 스캔 중)")
        pd.DataFrame(gk_results).to_csv(f"backup_date_{len(checked_ouids)}.csv", index=False, encoding="utf-8-sig")
        
    time.sleep(0.05) # 유저 한 명 끝날 때마다 서버 부하 방지용 짧은 휴식

# 4. 최종 저장
pd.DataFrame(gk_results).to_csv("Final_Raw_Data_With_Date_DeepScan.csv", index=False, encoding="utf-8-sig")
print("\n🎉 3월 26일 이후 매일매일의 데이터 싹쓸이 완료!")