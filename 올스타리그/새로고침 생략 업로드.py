import win32com.client
import os, time, requests, base64, subprocess, ctypes
from PIL import ImageGrab, Image

# ==========================================
# 1. 환경 설정
# ==========================================
EXCEL_FILE_PATH = r"C:\Users\원영이\Desktop\ATL AUTO\All-Star LEAGUE.xlsm"
IMGBB_API_KEY = "ae84f8a45971fc994c3a2ce9aa29c8f6"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MACRO_LIST = {
    "CopyRangeAsImage_1st_U42": "1st.jpg",
    "CopyRangeAsImage_2nd_U42": "2nd.jpg",
    "CopyRangeAsImage_FACUP_CM51": "fa.jpg",
    "CopyRangeAsImage_UCLGROUP_AO25": "uclg.jpg",
    "CopyRangeAsImage_UCLT_CM51": "uclt.jpg",
    "CopyRangeAsImage_UELT_CM51": "uelt.jpg",
    "CopyRangeAsImage_GOLDENBOOT_HE127": "gb.jpg",
    "CopyRangeAsImage_PLAYMAKER_HE127": "pm.jpg", # ✅ 8번째 시트 (Playmaker) 추가
}

# ==========================================
# 2. 기능 함수
# ==========================================

def clear_clipboard():
    try:
        ctypes.windll.user32.OpenClipboard(None)
        ctypes.windll.user32.EmptyClipboard()
        ctypes.windll.user32.CloseClipboard()
    except Exception as e: 
        print(f"⚠️ 클립보드 초기화 실패: {e}")

def upload_to_imgbb(image_path):
    url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as f:
            res = requests.post(url, {"key": IMGBB_API_KEY, "image": base64.b64encode(f.read())})
            if res.status_code == 200:
                return res.json()['data']['url']
            else:
                print(f"⚠️ 이미지 업로드 실패 (상태 코드: {res.status_code})")
    except Exception as e: 
        print(f"⚠️ ImgBB API 통신 오류: {e}")
    return None

def update_html(urls):
    t_path = os.path.join(BASE_DIR, "template.html")
    i_path = os.path.join(BASE_DIR, "index.html")
    
    if not os.path.exists(t_path): 
        print("⚠️ template.html 파일을 찾을 수 없습니다!")
        return

    with open(t_path, "r", encoding="utf-8") as f:
        content = f.read()

    mapping = {
        "{{LINK_1ST}}": "CopyRangeAsImage_1st_U42",
        "{{LINK_2ND}}": "CopyRangeAsImage_2nd_U42",
        "{{LINK_UCLG}}": "CopyRangeAsImage_UCLGROUP_AO25",
        "{{LINK_UCLT}}": "CopyRangeAsImage_UCLT_CM51",
        "{{LINK_UELT}}": "CopyRangeAsImage_UELT_CM51",
        "{{LINK_FA}}": "CopyRangeAsImage_FACUP_CM51",
        "{{LINK_GB}}": "CopyRangeAsImage_GOLDENBOOT_HE127",
        "{{LINK_PM}}": "CopyRangeAsImage_PLAYMAKER_HE127" # ✅ 8번째 HTML 매핑 추가
    }
    
    for tag, m_name in mapping.items():
        content = content.replace(tag, urls.get(m_name, ""))

    with open(i_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("🌐 index.html 갱신 완료!")

def git_push():
    print("🚚 GitHub 상태 확인 및 전송 중...")
    try:
        # 1. 변경된 파일이 있는지 확인 (git status --porcelain)
        # 결과가 비어있으면 변경 사항이 없는 것임
        status_check = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, text=True, cwd=BASE_DIR
        )
        
        if not status_check.stdout.strip():
            print("ℹ️ 변경된 데이터가 없습니다. (최신 상태 유지 중) GitHub 푸시를 건너뜁니다.")
            return

        # 2. 변경 사항이 있을 때만 동작
        subprocess.run(["git", "add", "."], check=True, cwd=BASE_DIR)
        msg = f"Optimize: {time.strftime('%H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=BASE_DIR)
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=BASE_DIR)
        print("🚀 GitHub 업데이트 성공!")
        
    except Exception as e: 
        print(f"⚠️ GitHub 푸시 중 문제 발생: {e}")

def main():
    print("🚀 [초고속 모드] 자동 중계 시스템 가동!")
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True
    
    wb = None
    try:
        wb = excel.Workbooks.Open(os.path.abspath(EXCEL_FILE_PATH))
        
        # ✅ 새로고침 및 대기 코드(wb.RefreshAll(), time.sleep) 제거됨
        
        final_urls = {}
        for m_name, f_name in MACRO_LIST.items():
            print(f"📸 {m_name} 캡처 및 최적화 중...")
            clear_clipboard()
            excel.Run(m_name)
            time.sleep(1.2)
            
            save_path = os.path.join(BASE_DIR, f_name)
            img = ImageGrab.grabclipboard()
            
            if img:
                # 🌈 [핵심] JPG 저장을 위해 RGB 모드로 변환 후 압축 저장
                img = img.convert("RGB")
                img.save(save_path, "JPEG", quality=100) # 화질 100% 수준으로 압축 (용량 대폭 감소)
                
                url = upload_to_imgbb(save_path)
                if url:
                    final_urls[m_name] = url
                    print(f"✅ 주소: {url}")
            else:
                print(f"⚠️ {m_name} 캡처 실패: 클립보드에 이미지가 없습니다.")
        
        if final_urls:
            update_html(final_urls)
            git_push()
            
        wb.Save()
        print("🟢 모든 작업이 완료되었습니다. (엑셀 창을 그대로 유지합니다)")
        
    except Exception as e:
        print(f"❌ 치명적 오류 발생: {e}")
    finally:
        # ✅ 엑셀 자동 종료(wb.Close, excel.Quit) 코드 제거됨
        pass

if __name__ == "__main__":
    main()