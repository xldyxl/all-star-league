import requests

# 1. 설정
api_key = "live_f4551344020f5d8e5aa2e29c8fea68b1cc76b722b41becd6437c639aef430e52efe8d04e6d233bd35cf2fabdeb93fb0d"
headers = {"x-nxopen-api-key": api_key}

# 터미널에 떴던 탈락 Match ID 중 하나를 가져옵니다.
m_id = "69eb029d6e6c8cc820a0d6b9" 

print(f"🕵️ Match ID [{m_id}]의 실제 데이터 구조를 까봅니다...\n")

res = requests.get(f"https://open.api.nexon.com/fconline/v1/match-detail?matchid={m_id}", headers=headers)
data = res.json()

m_infos = data.get('matchInfo', [])

for i, info in enumerate(m_infos):
    nick = info.get('nickname')
    ouid = info.get('ouid')
    print(f"[팀 {i+1}] 닉네임: {nick} / OUID: {ouid}")

print("\n--------------------------------------------------")