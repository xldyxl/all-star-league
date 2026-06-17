import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. 기본 설정
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

nickname = "UNIT"

# 내 OUID 가져오기
print("🔄 내 계정(OUID) 정보 불러오는 중...")
res_ouid = requests.get(f"https://open.api.nexon.com/fconline/v1/id?nickname={nickname}", headers=headers)
my_ouid = res_ouid.json().get('ouid')

# 2. 데이터 저장소 초기화
target_ouids = [my_ouid]
checked_ouids = set()
checked_matches = set()
gk_results = []

# 3. 수집 설정 (5,000명 / 4월 13일부터 현재까지)
TARGET_USER_COUNT = 5000

# 💡 오늘 기준으로 14일 전 날짜 계산
target_date_obj = datetime.now() - timedelta(days=14)
TARGET_START_DATE = target_date_obj.strftime("%Y-%m-%d")

print(f"\n--- 📅 {TARGET_START_DATE} ~ 오늘까지의 데이터 딥 스캔 시작 ---")
print(f"목표 유저 수: {TARGET_USER_COUNT}명")
print("⚠️ NoneType 에러 방지 로직이 적용되었습니다. 안전하게 스캔을 시작합니다.")

while len(target_ouids) > 0 and len(checked_ouids) < TARGET_USER_COUNT:
    current_ouid = target_ouids.pop(0)
    if current_ouid in checked_ouids: continue
    checked_ouids.add(current_ouid)
    
    offset = 0
    limit = 100 
    user_time_travel_done = False 
    
    while not user_time_travel_done:
        try:
            # 공식경기 데이터 호출
            res = requests.get(f"https://open.api.nexon.com/fconline/v1/user/match?ouid={current_ouid}&matchtype=50&offset={offset}&limit={limit}", headers=headers)
            
            if res.status_code == 429:
                print("⏳ API 한도 초과! 5초 대기 후 재시도...")
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
                
                # 🛑 타임머신 종료 조건 (설정된 날짜보다 이전이면 종료)
                if m_date < TARGET_START_DATE:
                    user_time_travel_done = True
                    break 
                
                m_infos = data.get('matchInfo', [])
                if len(m_infos) != 2: continue
                
                for i, team in enumerate(m_infos):
                    opp = m_infos[1] if i == 0 else m_infos[0]
                    
                    # 새로운 유저 수집 (거미줄 확장)
                    if team.get('ouid') not in checked_ouids: 
                        target_ouids.append(team.get('ouid'))
                    
                    # 🔍 [에러 방지] 데이터가 null(None)일 경우 0으로 치환
                    eff = opp.get('shoot', {}).get('effectiveShootTotal')
                    if eff is None: eff = 0
                    
                    goal = opp.get('shoot', {}).get('goalTotal')
                    if goal is None: goal = 0
                    
                    # 골키퍼 정보 추출
                    gk_id = None
                    gk_grade = 0
                    for p in team.get('player', []):
                        if p.get('spPosition') == 0:
                            gk_id = p.get('spId')
                            gk_grade = p.get('spGrade', 0)
                            break
                    
                    # 유효 데이터만 저장 (유효슈팅이 있는 경우만)
                    if gk_id and eff > 0:
                        gk_results.append({
                            '날짜': m_date, 
                            'GK_ID': gk_id, 
                            '강화단계': gk_grade, 
                            '피슈팅': eff, 
                            '선방': max(0, eff - goal)
                        })

            # 2주 기간이므로 인당 최대 500경기까지만 뒤짐
            offset += 100 
            if offset > 500: 
                break
                
        except Exception as e:
            # 개별 경기 오류 시 건너뛰고 계속 진행
            continue 

    # 유저 10명마다 현황 출력 및 백업 파일 생성
    if len(checked_ouids) % 10 == 0:
        print(f"📊 {len(checked_ouids)}명 스캔 완료... 누적 데이터 {len(gk_results)}건")
        pd.DataFrame(gk_results).to_csv(f"backup_5000_scan.csv", index=False, encoding="utf-8-sig")
        
    time.sleep(0.05) 

# 4. 최종 저장
final_filename = f"Final_2Weeks_5000Users_GK_Data.csv"
pd.DataFrame(gk_results).to_csv(final_filename, index=False, encoding="utf-8-sig")

print(f"\n🎉 모든 수집이 완료되었습니다!")
print(f"✅ 총 유저: {len(checked_ouids)}명 / 총 GK 데이터: {len(gk_results)}건")
print(f"💾 파일 저장 완료: {final_filename}")