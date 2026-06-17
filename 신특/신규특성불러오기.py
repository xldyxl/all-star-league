import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import glob
import re
import datetime

# 🎯 신규 특성 이미지 파일명 매핑 (F12 분석 적용)
TRAIT_IMG_MAP = {
    "trait_icon_50.png": "아크로바틱 피니셔",
    "trait_icon_51.png": "크로스 포쳐",
    "trait_icon_52.png": "라인 브레이커",
    "trait_icon_53.png": "와일드 태클러",
    "trait_icon_54.png": "체이서",
    "trait_icon_55.png": "2개의 심장",
    "trait_icon_56.png": "파이터",
    "trait_icon_57.png": "GK 빠른 반응",
    "trait_icon_59.png": "커맨더",
    "trait_icon_60.png": "GK 공중볼 장악",
    "trait_icon_62.png": "블로커",
    "trait_icon_63.png": "스피드스터",
    "trait_icon_64.png": "타이탄"
}

# 🎯 클럽 화이트리스트 필터링 목록
VALID_CLUBS = {
    "FC 우니온 베를린", "FC 쾰른", "FSV 마인츠", "19 New Generation", "20 New Generation", "2012 KOREAN HEROES", "21 KFA", "21 NEW GENERATION", "22 KFA", "22 New Generation", "23 Hard Worker", "23 New Generation", "24 Energetic Player", "AS 로마", "AS 모나코", "AS 생테티엔", "Back to Back", "Ballon d'Or", "Best of Europe", "Best of World Cup", "Captain", "Century Club", "Champions of Europe", "Competitors Of Continents", "Continental Heroes", "Decade", "Dramatic Comebacks", "European Best Stars", "FC Ambassador", "FC 낭트", "FC 로리앙", "FC 메스", "FC 바르셀로나", "FC 바젤", "FC 샬케", "FC 서울", "FC 아우크스부르크", "FC 안양", "FC 코펜하겐", "FC 포르투", "Football Association Champions", "Free Agent", "Golden Rookies", "Greatest Runner-Ups", "Heroes Of the Team", "Home Grown", "ICON", "ICON The Moment", "Journeyman", "Korea Heroes Debut", "KRC 겡크", "LA 갤럭시", "Legend of Europa", "Legend of the Loan", "Legendary Numbers", "LOSC 릴", "Loyal Heroes", "Man City Icon", "Medalist", "Moments of Glory", "Multi-League Champions", "National Hero Debut", "Nostalgia", "Number", "OGC 니스", "1PSV", "RB 라이프치히", "RC 랑스", "RCD 마요르카", "RCD 에스파뇰", "Returnees", "SC 프라이부르크", "SD 에이바르", "SD 우에스카", "SL 벤피카", "Spotlight", "SSC 나폴리", "Step Higher", "Team K League", "TEAM KOREA", "Team Korea Icon", "Top Transfer", "Tournament Best", "Tournament Champions", "TSG 호펜하임", "UEFA EURO", "Unexpected Transfer", "Unsung Players", "Veteran", "VfB 슈투트가르트", "VfL 볼프스부르크", "Warriors of Glory", "Winning Streak", "Wonderboys", "World Cup", "갈라타사라이", "강원 FC", "경남 FC", "광주 FC", "그라나다 CF", "김천 상무", "뉴캐슬 유나이티드", "대구 FC", "대전 하나 시티즌", "데포르티보 알라베스", "디나모 자그레브", "디나모 키이우", "라티움", "레드불 잘츠부르크", "레반테 UD", "레스터 시티", "레알 마드리드", "레알 바야돌리드", "레알 베티스", "레알 소시에다드", "레인저스", "롬바르디아 FC", "리버풀", "리즈 유나이티드", "맨체스터 시티", "맨체스터 유나이티드", "몽펠리에 HSC", "미들즈브러", "밀라노 FC", "바샥셰히르", "바이에른 뮌헨", "바이엘 04 레버쿠젠", "발렌시아 CF", "번리", "베르가모 칼초", "베르더 브레멘", "보루시아 도르트문트", "보루시아 묀헨글라트바흐", "볼로냐", "부산 아이파크", "부천 FC", "브라이턴 호브 앨비언", "블랙번 로버스", "비야레알 CF", "사수올로", "사우샘프턴", "산둥 타이산", "삼프도리아", "상하이 선화", "상하이 하이강", "샤흐타르 도네츠크", "서울 이랜드", "성남 FC", "세비야 FC", "셀타 비고", "셀틱", "셰필드 유나이티드", "수원 FC", "수원 삼성 블루윙즈", "스타드 랭스", "스타드 렌", "스타드 브레스트", "스토크 시티", "스트라스부르 알자스", "스파르타 프라하", "스페치아", "스포르팅 CP", "아르미니아 빌레펠트", "아스널", "아약스", "아인트라흐트 프랑크푸르트", "아틀레티코 마드리드", "아틀레틱 빌바오", "안산 그리너스 FC", "앙제 SCO", "애스턴 빌라", "에버턴", "엘라스 베로나", "엘체 CF", "오사수나", "올랭피크 리옹", "올랭피크 마르세유", "왓퍼드", "우디네세", "울버햄프턴 원더러스", "울산 현대", "울산 HD FC", "웨스트 브로미치 앨비언", "웨스트 햄 유나이티드", "유벤투스", "인천 유나이티드", "전남 드래곤즈", "전북 현대 모터스", "제노아", "제주 SK FC", "첼시", "충남 아산 축구단", "카디스 CF", "칼리아리", "크리스털 팰리스", "톈진 진먼후", "토리노", "토트넘 홋스퍼", "파르마", "파리 생제르맹", "페예노르트", "포항 스틸러스", "풀럼", "피오렌티나", "함부르크 SV", "헤르타 BSC", "헤타페 CF"
}

# 📁 저장 경로 설정
BASE_DIR = r"C:\Users\원영이\Desktop\파이썬 코딩\신특"
BACKUP_DIR = r"C:\Users\원영이\Desktop\파이썬 코딩\신특\backup"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

def find_id_file(search_dir):
    patterns = ["ID.xlsx - Sheet1.csv", "ID.csv", "ID.xlsx", "PlayerNameID.csv", "ID*.csv"]
    for pattern in patterns:
        search_path = os.path.join(search_dir, pattern)
        files = glob.glob(search_path)
        if files: return files[0]
    return None

file_path = find_id_file(BASE_DIR)
if not file_path:
    print(f"❌ ID 파일을 찾을 수 없습니다. '{BASE_DIR}' 폴더에 파일이 있는지 확인해주세요.")
    exit()

df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
id_col = 'ID' if 'ID' in df.columns else ('PlayerNameID' if 'PlayerNameID' in df.columns else df.columns[0])
unique_ids = df[id_col].dropna().unique()

options = Options()
options.add_experimental_option("detach", True)
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
options.add_argument('--start-maximized') 

driver = webdriver.Chrome(options=options)
driver.get("https://fconline.nexon.com/main/index")

print(f"\n✅ 파일 로드 성공: {file_path}")
print(f"🎯 총 {len(unique_ids)}명의 선수를 스캔합니다.")
print("\n" + "★"*45)
print("🛡️ [백그라운드 스캔 모드 활성화]")
print("이제 마우스 매크로가 필요 없습니다. 크롤러가 켜져 있는 동안")
print("다른 창에서 자유롭게 작업하셔도 됩니다!")
print("★"*45 + "\n")

input("준비가 완료되었다면 아무 창에서나 엔터를 눌러 수집을 시작합니다...")

if len(driver.window_handles) > 1:
    driver.switch_to.window(driver.window_handles[-1])

final_results = []
for idx, spid in enumerate(unique_ids):
    try:
        url = f"https://fconline.nexon.com/DataCenter/PlayerInfo?spid={int(spid)}&n1Strong=1"
        driver.get(url)
        time.sleep(1.5) # 페이지 기본 로딩 대기 (클릭 불필요)
        
        # HTML 소스 통째로 가져오기
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            html_source = driver.page_source
            name = driver.find_element(By.CLASS_NAME, 'name').text.strip()
        except:
            time.sleep(1.0)
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            html_source = driver.page_source
            name = driver.find_element(By.CLASS_NAME, 'name').text.strip()

        # 1. 🌟 선수 포지션 추출 (정규식 활용하여 주 포지션 한 개 추출)
        position = "알수없음"
        pos_match = re.search(r'\b(GK|ST|CF|LW|RW|CM|CAM|CDM|LM|RM|CB|RB|LB|RWB|LWB)\b', page_text)
        if pos_match:
            position = pos_match.group(1)

        # 2. 신규 특성 추출 (🔥 분석해주신 이미지 파일명 방식 적용)
        owned_traits = []
        for img_file, trait_name in TRAIT_IMG_MAP.items():
            if img_file in html_source:  # 소스코드 내에 해당 이미지 파일명이 존재하면
                owned_traits.append(trait_name)
        
        traits_str = ", ".join(owned_traits) if owned_traits else "없음"
        
        # 3. 국가 추출
        nation = "알수없음"
        try:
            nation_elements = driver.find_elements(By.CSS_SELECTOR, '.nation')
            for el in nation_elements:
                if el.text.strip():
                    nation = el.text.strip()
                    break
            
            if nation == "알수없음":
                nation_img = driver.find_element(By.XPATH, "//img[contains(@src, 'nation') or contains(@alt, '국가')]")
                nation = nation_img.find_element(By.XPATH, "./parent::*").text.strip()
                if not nation:
                    nation = nation_img.find_element(By.XPATH, "./following-sibling::span").text.strip()
        except:
            pass

        # 4. 주발/약발 추출
        preferred_foot = ""
        weak_foot = ""
        foot_match = re.search(r'L\s*(\d)\s*[-–—]\s*R\s*(\d)', page_text)
        if foot_match:
            l_val = int(foot_match.group(1))
            r_val = int(foot_match.group(2))
            
            if l_val == 5 and r_val == 5:
                preferred_foot = "양발"
                weak_foot = 5
            elif l_val > r_val:
                preferred_foot = "왼발"
                weak_foot = r_val
            elif r_val > l_val:
                preferred_foot = "오른발"
                weak_foot = l_val
            else:
                l_bold = re.search(r'(class="[^"]*bold[^"]*"|<strong>|<b\b[^>]*>)\s*L', html_source, re.IGNORECASE)
                if l_bold:
                    preferred_foot = "왼발"
                else:
                    preferred_foot = "오른발" 
                weak_foot = l_val

        # 5. 클럽 경력 추출 (완전 탐색 방식)
        clubs = []
        try:
            all_tds = driver.find_elements(By.TAG_NAME, "td")
            for td in all_tds:
                c_name = td.text.strip()
                if c_name in VALID_CLUBS and c_name not in clubs:
                    clubs.append(c_name)
            
            if not clubs:
                lines = page_text.split('\n')
                for line in lines:
                    c_name = line.strip()
                    if c_name in VALID_CLUBS and c_name not in clubs:
                        clubs.append(c_name)
        except Exception as e:
            pass

        print(f"✅ [{idx+1}/{len(unique_ids)}] {name} | 포지션: {position} | 국가: {nation} | 특성: {traits_str} | 클럽수: {len(clubs)}")
        
        # 🌟 결과 데이터에 '포지션' 필드 추가
        player_data = {
            '선수ID': int(spid), 
            '선수이름': name, 
            '포지션': position, 
            '보유신규특성': traits_str,
            '국가': nation,
            '주발': preferred_foot,
            '약발': weak_foot
        }
        
        for i, club in enumerate(clubs):
            player_data[f'클럽{i+1}'] = club
            
        final_results.append(player_data)
        
        # 6. 50명마다 백업 데이터 저장
        if (idx + 1) % 50 == 0:
            backup_file = os.path.join(BACKUP_DIR, f"backup_{idx+1}명완료.csv")
            backup_df = pd.DataFrame(final_results)
            backup_max_clubs = max((sum(1 for k in res.keys() if str(k).startswith('클럽')) for res in final_results), default=0)
            backup_cols = ['선수ID', '선수이름', '포지션', '보유신규특성', '국가', '주발', '약발'] + [f'클럽{i}' for i in range(1, backup_max_clubs + 1)]
            for col in backup_cols:
                if col not in backup_df.columns:
                    backup_df[col] = ""
            backup_df = backup_df[backup_cols].fillna("")
            backup_df.to_csv(backup_file, index=False, encoding="utf-8-sig")
            print(f"💾 [자동 백업] {idx+1}명 데이터 백업 완료")
        
    except Exception as e:
        print(f"❌ ID {spid} 분석 중 오류 발생 (건너뜀)")
        final_results.append({
            '선수ID': int(spid), 
            '선수이름': "Error", 
            '포지션': "Error",
            '보유신규특성': "Error",
            '국가': "", '주발': "", '약발': ""
        })

# 7. 최종 결과 저장
output_file = os.path.join(BASE_DIR, "신규특성_최종_수집결과.csv")
result_df = pd.DataFrame(final_results)

max_clubs = 0
for res in final_results:
    club_count = sum(1 for k in res.keys() if str(k).startswith('클럽'))
    if club_count > max_clubs:
        max_clubs = club_count

# 🌟 최종 저장 컬럼에도 '포지션' 추가
columns = ['선수ID', '선수이름', '포지션', '보유신규특성', '국가', '주발', '약발']
for i in range(1, max_clubs + 1):
    columns.append(f'클럽{i}')

for col in columns:
    if col not in result_df.columns:
        result_df[col] = ""

result_df = result_df[columns]
result_df.fillna("", inplace=True) 

try:
    result_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n🎉 백그라운드 수집이 완료되었습니다!")
    print(f"📁 최종 결과 저장 완료: '{output_file}'")
except PermissionError:
    print(f"\n🚨 [알림] 엑셀 파일({output_file})이 켜져 있어서 덮어쓸 수 없습니다.")
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    alt_file = os.path.join(BASE_DIR, f"신규특성_최종_수집결과_{now}.csv")
    result_df.to_csv(alt_file, index=False, encoding="utf-8-sig")
    print(f"📁 임시로 새 이름으로 저장했습니다: '{alt_file}'")