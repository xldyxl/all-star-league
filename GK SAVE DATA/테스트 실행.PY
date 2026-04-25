import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re  # 🔥 텍스트 안에서 숫자만 쏙 빼내기 위한 모듈 추가

# 1. 파일 설정
file_name = r"C:\Users\원영이\Desktop\파이썬 코딩\GK SAVE DATA\PlayerNameID.csv"
id_column_name = "PlayerNameID" 

print(f"📊 '{file_name}' 파일을 읽어옵니다...")
df = pd.read_csv(file_name)
unique_ids = df[id_column_name].unique()
print(f"🧤 검색할 골키퍼는 총 {len(unique_ids)}명입니다.")

driver = webdriver.Chrome()
driver.get("https://fconline.nexon.com/main/index")

print("\n🚨 [주의] 크롬 창이 열리면 이벤트 팝업창의 'X'만 눌러주세요!")
print("⏳ 10초 대기 중...\n")
time.sleep(10) 

final_results = []

for spid in unique_ids:
    try:
        if not str(spid).isdigit(): continue
            
        url = f"https://fconline.nexon.com/DataCenter/PlayerInfo?spid={int(spid)}&n1Strong=1"
        driver.get(url)
        time.sleep(1.2) 
        
        # 1. 급여 추출
        try:
            pay = driver.find_element(By.CLASS_NAME, 'pay').text.strip()
        except:
            pay = "N/A"
            
        # 2. 오버롤 6중 그물망 로직
        ovr = "N/A"
        ovr_selectors = [
            (By.XPATH, "//*[text()='GK']/following::*[contains(@class, 'num')][1]"), 
            (By.XPATH, "//*[contains(text(), 'GK')]/following-sibling::*[contains(@class, 'num')]"),
            (By.CSS_SELECTOR, ".ovr_info .num"), 
            (By.CSS_SELECTOR, ".ovr"), 
            (By.CSS_SELECTOR, ".p_position .num"), 
            (By.CSS_SELECTOR, ".info_wrap .num") 
        ]
        
        for by_type, selector in ovr_selectors:
            try:
                candidate = driver.find_element(by_type, selector).text.strip()
                if candidate.isdigit() and int(candidate) > 0:
                    ovr = candidate
                    break 
            except:
                continue
                
        # 3. 🔥 키(신장) 그물망 로직 (NEW!)
        height = "N/A"
        height_selectors = [
            (By.CSS_SELECTOR, ".info_wrap .height"), # 넥슨의 전형적인 키 클래스
            (By.CSS_SELECTOR, ".height"),
            (By.XPATH, "//*[contains(text(), 'cm')]") # 'cm' 글자가 포함된 모든 요소 찌르기
        ]
        
        for by_type, selector in height_selectors:
            try:
                candidate = driver.find_element(by_type, selector).text.strip()
                
                # 정규식을 사용해 '188cm', '신장 188 cm' 등에서 3자리 숫자만 쏙 빼오기
                match = re.search(r'(\d{3})\s*cm', candidate.lower())
                if match:
                    height = match.group(1)
                    break
                # 만약 cm가 안 붙어있고 상식적인 키 범위(160~210)의 숫자로만 되어있다면 추출
                elif candidate.isdigit() and 160 < int(candidate) < 210:
                    height = candidate
                    break
            except:
                continue
            
        print(f"✅ ID {spid} 완료 | 급여: {pay} | OVR: {ovr} | 키: {height}cm")
        final_results.append({'PlayerNameID': spid, '급여': pay, 'OVR': ovr, '키': height})
        
    except Exception as e:
        print(f"❌ ID {spid} 처리 중 오류 발생")
        final_results.append({'PlayerNameID': spid, '급여': "에러", 'OVR': "에러", '키': "에러"})

driver.quit()

# 4. 결과 저장
result_df = pd.DataFrame(final_results)
output_file = "GK_Pay_OVR_Height_Final.csv" # 파일명도 키 포함으로 변경!
result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n🎉 수집 완료! '{output_file}' 파일이 생성되었습니다.")