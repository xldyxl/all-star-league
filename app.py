import streamlit as st
import pandas as pd
import os

# 1. 모바일에 적합하게 기본 설정 (layout="wide" 제거하여 세로형에 맞춤)
st.set_page_config(page_title="올스타리그 ELO 랭킹", page_icon="🏆")

st.title("🏆 올스타리그 랭킹")
st.caption("최신 경기 결과가 반영된 실시간 ELO 랭킹입니다.")

# 엑셀 파일 절대 경로
EXCEL_FILE_PATH = "Ranking_Data.xlsx"

try:
    # 2. 데이터 불러오기
    df_ranking = pd.read_excel(
        EXCEL_FILE_PATH, 
        sheet_name="랭킹(ELO)", 
        usecols="A:G"
    )
    
    # 빈 데이터(닉네임 없는 행) 제거 및 순위 열 추가
    df_ranking = df_ranking.dropna(subset=['닉네임'])
    df_ranking.insert(0, '순위', range(1, len(df_ranking) + 1))
    
    # 3. 모바일 화면에 맞게 불필요한 열 숨기기 및 이름 줄이기
    # 스마트폰 세로 화면은 좁기 때문에 꼭 필요한 정보만 추려냅니다.
    mobile_df = df_ranking[['순위', '닉네임', '팀명', '17시즌 ELO', '+-']].copy()
    mobile_df.rename(columns={'17시즌 ELO': 'ELO', '+-': '변동'}, inplace=True)
    
    # ELO 등락 색상 기호 함수
    def color_elo_change(val):
        try:
            if float(val) > 0:
                return 'color: #ff4b4b; font-weight: bold;' # 상승 (빨강)
            elif float(val) < 0:
                return 'color: #1f77b4; font-weight: bold;' # 하락 (파랑)
            else:
                return 'color: gray;' 
        except:
            return ''

    # 4. 스타일 및 포맷 적용 (소수점 첫째 자리까지만 표시하여 가로 폭 절약)
    styled_ranking = mobile_df.style.map(
        color_elo_change, subset=['변동']
    ).format({
        "ELO": "{:.1f}",
        "변동": "{:+.1f}"
    })
    
    # 5. 화면에 표 렌더링
    st.dataframe(
        styled_ranking, 
        hide_index=True,          
        use_container_width=True, 
        height=700 # 모바일에서 위아래로 스크롤하기 좋게 세로 길이 확보
    )
    
except FileNotFoundError:
    st.error(f"엑셀 파일을 찾을 수 없습니다. 경로를 확인해주세요: {EXCEL_FILE_PATH}")
except Exception as e:
    st.error(f"랭킹 데이터를 불러오는 중 오류가 발생했습니다: {e}")