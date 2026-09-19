import win32com.client
import os, time, subprocess, ctypes, shutil

# ==========================================
# 1. 환경 설정
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE_PATH = os.path.join(BASE_DIR, "All-Star LEAGUE.xlsm")

# 🚨 ELO 랭킹용 깃허브 폴더가 있는 PC의 실제 경로
ELO_REPO_DIR = r"C:\Users\원영이\Desktop\AllStar-Ranking-ELO-"

# 실제 랭킹 데이터가 있는 시트 이름
TARGET_SHEET_NAME = "랭킹(ELO)"

def clear_clipboard():
    try:
        ctypes.windll.user32.OpenClipboard(None)
        ctypes.windll.user32.EmptyClipboard()
        ctypes.windll.user32.CloseClipboard()
    except Exception as e: 
        print(f"⚠️ 클립보드 초기화 실패: {e}")

# 🔄 랭킹 데이터 자동 추출 함수
def extract_ranking_data(excel, wb):
    print(f"\n📊 [{TARGET_SHEET_NAME}] 시트 데이터를 Ranking_Data.xlsx로 추출합니다...")
    try:
        source_sheet = wb.Sheets(TARGET_SHEET_NAME)
        new_wb = excel.Workbooks.Add()
        
        source_sheet.UsedRange.Copy()
        new_wb.Sheets(1).Range("A1").PasteSpecial(Paste=-4163) # xlPasteValues (값만 붙여넣기)
        
        save_path = os.path.join(BASE_DIR, "Ranking_Data.xlsx")
        
        # 기존 임시 파일이 있다면 삭제
        if os.path.exists(save_path):
            os.remove(save_path)
            
        new_wb.SaveAs(save_path, FileFormat=51)
        new_wb.Close(False) 
        
        clear_clipboard()
        print("   ✅ 추출 완료 (임시 저장)")
        return save_path
    except Exception as e:
        print(f"   ⚠️ 랭킹 데이터 추출 실패: {e}")
        return None

# 🚀 ELO 저장소로 엑셀 복사 및 푸시하는 함수
def git_push_elo_repo(source_excel_path):
    print("\n🚚 [Streamlit ELO 저장소] Ranking_Data.xlsx 전송 중...")
    if not os.path.exists(ELO_REPO_DIR):
        print("   ⚠️ ELO 저장소 경로를 찾을 수 없습니다. 코드 상단의 ELO_REPO_DIR을 확인해주세요.")
        return
        
    target_excel_path = os.path.join(ELO_REPO_DIR, "Ranking_Data.xlsx")
    
    try:
        # 1. 파일 복사
        shutil.copy2(source_excel_path, target_excel_path)
        print(f"   ✅ ELO 폴더로 엑셀 복사 완료")
        
        # 2. 깃허브 최신화 (웹에서 변경된 내용이 있으면 먼저 가져와서 충돌 방지)
        try:
            subprocess.run(["git", "pull", "origin", "main", "--no-edit"], check=False, cwd=ELO_REPO_DIR)
        except Exception:
            pass
            
        # 3. 깃허브 푸시
        subprocess.run(["git", "add", "Ranking_Data.xlsx"], check=True, cwd=ELO_REPO_DIR)
        msg = f"Update: Ranking Data ({time.strftime('%H:%M:%S')})"
        subprocess.run(["git", "commit", "--allow-empty", "-m", msg], check=True, cwd=ELO_REPO_DIR)
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=ELO_REPO_DIR)
        print("   🚀 ELO 깃허브(Streamlit) 업데이트 성공!")
    except Exception as e:
        print(f"   ⚠️ ELO 저장소 푸시 실패: {e}")

def main():
    print("🚀 랭킹 데이터 동기화 시스템 가동!")
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True
    excel.WindowState = -4143
    
    wb = None
    try:
        wb = excel.Workbooks.Open(os.path.abspath(EXCEL_FILE_PATH))
        
        # ✅ 랭킹 데이터 추출 후 Streamlit(ELO) 저장소로 푸시
        extracted_excel_path = extract_ranking_data(excel, wb)
        if extracted_excel_path:
            git_push_elo_repo(extracted_excel_path)
            
        wb.Save()
        print("\n🟢 랭킹 업데이트 작업이 정상적으로 완료되었습니다.")
        
    except Exception as e:
        print(f"❌ 치명적 오류 발생: {e}")
    finally:
        pass

if __name__ == "__main__":
    main()