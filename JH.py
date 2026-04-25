import streamlit as st

st.title("⚽ FC 온라인 집중훈련 시뮬레이터")

# 1. 선수 및 기본 정보 설정
col1, col2 = st.columns(2)
with col1:
    player_name = st.selectbox("선수 선택", ["LE 미키타리안", "JVA 바조", "UT 파바르"])
    enchant = st.slider("강화 단계", 1, 10, 10)
with col2:
    team_color = st.number_input("팀컬러 가산치", value=8)

# 2. 집중훈련 입력 (엑셀의 그 부분!)
st.subheader("📊 집중훈련 설정")
speed = st.slider("속력", 0, 10, 2)
acceleration = st.slider("가속력", 0, 10, 2)

# 3. 계산 로직 (여기에 엑셀 수식을 넣으시면 됩니다)
# 예: 속력 스탯 = 기본값 + 강화효과 + 팀컬러 + (집중훈련 * 가중치)
total_speed = 115 + (enchant * 2) + team_color + speed 

st.metric(label="최종 속력", value=total_speed)

# 4. 재화 계산
total_cp = speed * 2000 # 실제 수식으로 대체 필요
st.warning(f"소모되는 총 CP: {total_cp}")