from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time
import re

# 1. 크롬 브라우저 실행 및 데이터센터 접속
print("🚀 크롬 브라우저를 실행합니다...")
driver = webdriver.Chrome()
driver.get("https://fconline.nexon.com/DataCenter/Player")

# 2. 사용자 개입 대기 (이 타이밍에 원하는 선수를 새 탭으로 다 띄워주세요!)
print("\n==================================================")
print("🌐 넥슨 데이터센터가 열렸습니다.")
print("1. 추출할 선수들의 상세 페이지를 새 탭(Ctrl+클릭)으로 모두 열어주세요.")
print("2. (10개든 100개든 원하는 만큼 띄워두시면 됩니다.)")
print("==================================================\n")

input("👉 탭을 모두 여셨다면, 여기(콘솔창)를 클릭하고 [Enter] 키를 누르세요! 추출을 시작합니다...")

# 3. 열려있는 모든 탭(핸들) 가져오기
window_handles = driver.window_handles
data_list = []

print(f"\n🔍 총 {len(window_handles)}개의 탭이 감지되었습니다. 스캔을 시작합니다...")

# 4. 탭을 하나씩 순회하며 데이터 추출 후 닫기
for handle in window_handles:
    # 해당 탭으로 화면 전환
    driver.switch_to.window(handle)
    time.sleep(0.5) # 페이지가 뜰 때까지 아주 살짝만 대기
    
    current_url = driver.current_url

    # 메인 페이지나 검색 페이지 등 '선수 상세 페이지'가 아니면 탭 닫고 넘어가기
    if "PlayerInfo" not in current_url:
        driver.close() 
        continue

    try:
        # 선수 이름 추출
        player_name_element = driver.find_element(By.CSS_SELECTOR, ".name")
        player_name = player_name_element.text.strip()

        # 💡 [핵심 변경점] URL에서 SPID 직접 추출
        # 주소창 문자열에서 'spid=숫자' 형태를 찾아 숫자만 깔끔하게 뽑아냅니다.
        spid_match = re.search(r'spid=(\d+)', current_url, re.IGNORECASE)
        
        if spid_match:
            spid = spid_match.group(1)
            data_list.append({"SPID": spid, "선수이름": player_name})
            print(f"✅ 추출 완료: {player_name} (SPID: {spid})")
        else:
            print(f"⚠️ {player_name} 선수의 SPID를 주소창(URL)에서 찾지 못했습니다.")

    except Exception as e:
        print(f"❌ 이 탭에서 정보를 찾을 수 없습니다. 페이지 로딩 문제일 수 있습니다.")
    
    finally:
        # 정보 추출이 끝났든 에러가 났든 해당 탭은 닫습니다.
        driver.close()

# 남아있는 브라우저 프로세스 완전 종료
try:
    driver.quit()
except:
    pass

# 5. 엑셀 파일로 저장
if data_list:
    df = pd.DataFrame(data_list)
    df.to_excel("선수_SPID_목록.xlsx", index=False)
    print("\n🎉 모든 작업이 끝났습니다! '선수_SPID_목록.xlsx' 파일을 열어보세요.")
else:
    print("\n😥 추출된 데이터가 없습니다. 탭을 제대로 열었는지 확인해 주세요.")