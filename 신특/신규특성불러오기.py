import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import glob

# 🎯 구단주님이 업데이트하신 신규 특성 13종 (정확한 명칭)
TARGET_TRAITS = [
    "블로커", "체이서", "파이터", "와일드 태클러", "타이탄", "커맨더",
    "크로스 포쳐", "아크로바틱 피니셔", "스피드스터", "라인 브레이커", "2개의 심장",
    "GK 공중볼 장악", "GK 빠른 반응"
]

def find_id_file():
    # 파일명 후보들 확인 (ID.xlsx - Sheet1.csv 우선)
    patterns = ["ID.xlsx - Sheet1.csv", "ID.csv", "ID.xlsx", "PlayerNameID.csv", "ID*.csv"]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files: return files[0]
    return None

file_path = find_id_file()
if not file_path:
    print("❌ ID 파일을 찾을 수 없습니다. 파일명을 확인해주세요.")
    exit()

# 1. 데이터 로드
df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
id_col = 'ID' if 'ID' in df.columns else ('PlayerNameID' if 'PlayerNameID' in df.columns else df.columns[0])
unique_ids = df[id_col].dropna().unique()

# 2. 로봇 설정
options = Options()
options.add_experimental_option("detach", True)
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
options.add_argument('--start-maximized') 

driver = webdriver.Chrome(options=options)
driver.get("https://fconline.nexon.com/main/index")

print(f"\n✅ 파일 로드 성공: {file_path}")
print(f"🎯 총 {len(unique_ids)}명의 선수를 정밀 스캔합니다.")
print("\n" + "★"*45)
print("🛡️ [작전 실행 준비]")
print("1. 외부 매크로 소프트웨어를 [X:1377, Y:998] 무한 클릭으로 설정하세요.")
print("2. 창이 열리면 상세 페이지까지 직접 이동 후 여기서 [엔터]를 누르세요.")
print("3. 로봇이 페이지를 넘기면, 구단주님의 매크로가 화면을 뚫어줄 겁니다.")
print("★"*45 + "\n")

input("준비가 완료되었다면 엔터를 눌러 수집을 시작합니다...")

# 탭 전환 (구단주님이 보고 계신 최신 탭으로 시선 고정)
if len(driver.window_handles) > 1:
    driver.switch_to.window(driver.window_handles[-1])

final_results = []
for idx, spid in enumerate(unique_ids):
    try:
        url = f"https://fconline.nexon.com/DataCenter/PlayerInfo?spid={int(spid)}&n1Strong=1"
        
        # 🔗 페이지 이동
        driver.get(url)
        
        # ⏳ 구단주님의 매크로가 클릭하여 화면을 띄울 수 있도록 대기 (2.5초)
        # 로딩이 느리다면 이 시간을 더 늘려도 됩니다.
        time.sleep(2.5) 
        
        # 데이터 수집 (상세페이지 텍스트 스캔)
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            owned_traits = [trait for trait in TARGET_TRAITS if trait in page_text]
            traits_str = ", ".join(owned_traits) if owned_traits else "없음"
            
            # 이름/시즌 수집
            name = driver.find_element(By.CLASS_NAME, 'name').text.strip()
            season = driver.find_element(By.CSS_SELECTOR, '.season img').get_attribute('alt')
        except:
            # 혹시나 매크로 클릭이 늦어져서 로딩이 안 됐을 경우 1초 더 대기 후 재시도
            time.sleep(1.5)
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            owned_traits = [trait for trait in TARGET_TRAITS if trait in page_text]
            traits_str = ", ".join(owned_traits) if owned_traits else "없음"
            name = driver.find_element(By.CLASS_NAME, 'name').text.strip()
            season = driver.find_element(By.CSS_SELECTOR, '.season img').get_attribute('alt')

        print(f"✅ [{idx+1}/{len(unique_ids)}] {season} {name} | 신규특성: {traits_str}")
        final_results.append({'ID': spid, '시즌': season, '선수명': name, '신규특성': traits_str})
        
    except Exception as e:
        print(f"❌ ID {spid} 분석 중 오류 발생 (건너뜀)")
        final_results.append({'ID': spid, '시즌': "Error", '선수명': "Error", '신규특성': "Error"})

# 3. 결과 저장
output_file = "신규특성_최종_수집결과.csv"
pd.DataFrame(final_results).to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n🎉 모든 데이터 수집이 완료되었습니다!")
print(f"📁 결과 파일: '{output_file}'")
driver.quit()