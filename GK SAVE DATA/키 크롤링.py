import pandas as pd
from selenium import webdriver
import time
import re

# 1. 파일 설정 (원영님의 골키퍼 ID 리스트)
file_name = "PlayerNameID.csv" 
id_column_name = "PlayerNameID" 

print(f"📊 '{file_name}' 파일에서 ID를 읽어옵니다...")
df = pd.read_csv(file_name)

print(f"🧤 총 {len(df)}명의 골키퍼 '키(cm)' 단독 추출을 시작합니다!")

# 2. 크롬 실행
driver = webdriver.Chrome()
driver.get("https://fconline.nexon.com/main/index")

print("\n🚨 [주의] 크롬 창이 열리면 이벤트 팝업창의 'X'만 눌러주세요!")
print("⏳ 10초 대기 중...\n")
time.sleep(10) 

# 결과를 담을 빈 리스트
height_results = []

for index, row in df.iterrows():
    spid = row[id_column_name]
    
    try:
        # ID가 숫자가 아니면 패스
        if not str(spid).isdigit(): 
            continue
            
        url = f"https://fconline.nexon.com/DataCenter/PlayerInfo?spid={int(spid)}&n1Strong=1"
        driver.get(url)
        
        # 정보 하나만 찾으면 되니까 로딩 대기 시간 단축!
        time.sleep(0.8) 
        
        html = driver.page_source
        
        # 🔥 키(신장) 정규표현식 스캔
        height = "N/A"
        height_match = re.search(r'(1[6-9]\d|2[0-2]\d)\s*cm', html, re.IGNORECASE)
        if height_match:
            height = height_match.group(1)
            
        print(f"✅ ID {spid} 완료 | 키: {height}cm")
        height_results.append({'PlayerNameID': spid, '키(cm)': height})
        
    except Exception as e:
        print(f"❌ ID {spid} 실패")
        height_results.append({'PlayerNameID': spid, '키(cm)': "에러"})

driver.quit()

# 3. 새로운 파일로 깔끔하게 저장
result_df = pd.DataFrame(height_results)
output_file = "GK_Height_Only.csv" 
result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n🎉 스피드 스캔 완료! '{output_file}' 파일이 생성되었습니다.")