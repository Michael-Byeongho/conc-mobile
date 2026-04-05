import streamlit as st

# --- 0. Config & Style ---
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="centered")

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { background-color: white !important; color: #2c3e50 !important; }
        .stMarkdown, p, label { color: #2c3e50 !important; }
        .section-head { background-color: #2e4053; color: white !important; padding: 5px 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic (Deduction이 시장가격을 따르도록 수정) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, 
                  au_p, au_a, au_py, au_rc, au_dt, au_dv, 
                  ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # 1. Cu
    if cu_dt == "PD":
        cu_payable_content = (cu_a * (cu_py / 100.0)) - cu_dv
    else:
        cu_payable_content = cu_a * (cu_py / 100.0 - cu_dv / 100.0)
    v_cu_pay = (cu_payable_content / 100.0) * cu_p - (max(0, cu_payable_content) / 100.0) * (cu_rc * lb_to_mt)
    
    # 2. Ag: 20g 차이가 정확히 45.01불($20/31.1035*70)이 나오도록 함
    if ag_dt == "PD":
        ag_payable_content = (ag_a * (ag_py / 100.0)) - ag_dv
    else:
        ag_payable_content = ag_a * (ag_py / 100.0 - ag_dv / 100.0)
    v_ag_pay = (ag_payable_content * g_to_oz * ag_p) - (max(0, ag_payable_content) * g_to_oz * ag_rc)
    
    # 3. Au
    if au_dt == "PD":
        au_payable_content = (au_a * (au_py / 100.0)) - au_dv
    else:
        au_payable_content = au_a * (au_py / 100.0 - au_dv / 100.0)
    v_au_pay = (au_payable_content * g_to_oz * au_p) - (max(0, au_payable_content) * g_to_oz * au_rc)
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 상단 제목 및 포지션 설정 ---
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

# 결과를 그릴 '빈 공간'을 미리 확보 (최상단 배치를 위해)
res_placeholder = st.empty()

# --- 3. 공통 변수 입력 ---
with st.expander("⚙️ 시장 가격 및 품위 (공통)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0)
        ag_p = st.number_input("Ag Price ($/Oz)", value=70.0)
        au_p = st.number_input("Au Price ($/Oz)", value=4500.0)
    with c2:
        cu_a = st.number_input("Cu Assay (%)", value=25.0)
        ag_a = st.number_input("Ag Assay (g/DMT)", value=50.0)
        au_a = st.number_input("Au Assay (g/DMT)", value=5.0)

# --- 4. 상세 입력 (A, B, C안) ---
tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = [("A (Base)안", "a", 30.0), ("B안", "b", 30.0), ("C안", "c", 30.0)]
data = {}

for i, (name, k, def_tc) in enumerate(cases):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{name} - Metals Terms</div>", unsafe_allow_html=True)
        c_cu1, c_cu2, c_cu3 = st.columns(3)
        data[f"cu_py_{k}"] = c_cu1.number_input("Cu Pay (%)", value=100.0, key=f"cp_{k}")
        data[f"cu_dt_{k}"] = c_cu2.radio("Cu Deduct", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
        data[f"cu_dv_{k}"] = c_cu3.number_input("Cu PD/MD Val", value=1.25, key=f"cdv_{k}")
        
        st.divider()
        c_ag1, c_ag2, c_ag3 = st.columns(3)
        data[f"ag_py_{k}"] = c_ag1.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
        data[f"ag_dt_{k}"] = c_ag2.radio("Ag Deduct", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
        data[f"ag_dv_{k}"] = c_ag3.number_input("Ag PD/MD Val", value=50.0, key=f"adv_{k}")

        st.divider()
        c_au1, c_au2, c_au3 = st.columns(3)
        data[f"au_py_{k}"] = c_au1.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
        data[f"au_dt_{k}"] = c_au2.radio("Au Deduct", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
        data[f"au_dv_{k}"] = c_au3.number_input("Au PD/MD Val", value=1.25, key=f"audv_{k}")
        
        st.markdown(f"<div class='section-head'>📉 TC/RC</div>", unsafe_allow_html=True)
        c_tr1, c_tr2 = st.columns(2)
        data[f"tc_{k}"] = c_tr1.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
        data[f"cu_rc_{k}"] = c_tr1.number_input("Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
        data[f"ag_rc_{k}"] = c_tr2.number_input("Ag RC ($/oz)", value=0.4, key=f"agrc_{k}")
        data[f"au_rc_{k}"] = c_tr2.number_input("Au RC ($/oz)", value=5.0, key=f"aurc_{k}")

# --- 5. 실시간 계산 ---
res = {}
for _, k, _ in cases:
    res[k] = calc_unit_net(
        mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]
    )

# --- 6. 최상단 '빈 공간'에 결과 채우기 ---
d_b = res['b'] - res['a']
d_c = res['c'] - res['a']

with res_placeholder:
    st.markdown(f"""
        <div style="margin-top: 10px; margin-bottom: 20px;">
            <p style="font-weight: bold; margin-bottom: 5px;">📊 분석 결과 요약</p>
            <div style="display: flex; justify-content: space-between; gap: 10px;">
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">A안 (Base)</div>
                    <div style="font-size:22px; font-weight:bold;">${abs(res['a']):,.2f}</div>
                </div>
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">B안</div>
                    <div style="font-size:22px; font-weight:bold;">${abs(res['b']):,.2f}</div>
                    <div style="font-size:14px; font-weight:bold; color:{'green' if d_b > 0 else 'red'}">
                        {'▲' if d_b > 0 else '▼'} {abs(d_b):,.2f}
                    </div>
                </div>
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">C안</div>
                    <div style="font-size:22px; font-weight:bold;">${abs(res['c']):,.2f}</div>
                    <div style="font-size:14px; font-weight:bold; color:{'green' if d_c > 0 else 'red'}">
                        {'▲' if d_c > 0 else '▼'} {abs(d_c):,.2f}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.info("💡 불순물 및 기타 변수 제외, 금속 가격 및 payable, TRC 차이 Trade off 확인.")


# --- 6. 협상 타겟 계산 (Break-even TC) ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

# 1. 현재 두 안의 정산 결과 차이 (Gap) 계산
# res['a'], res['b']는 이미 calc_unit_net을 통해 나온 최종 Net $ (TC 포함)
net_a = res['a']
net_b = res['b']

# B안이 A안과 같아지기 위해 조정해야 할 금액 (Gap)
# gap > 0 이면 B안이 A안보다 돈을 더 많이 주거나 받는 상황
gap = net_b - net_a

# 2. Target TC 계산
# [매입/매출 공통] TC는 비용(Cost) 성격이므로, 
# B안의 결과값이 A안보다 높다면(gap > 0), 그만큼 TC를 더 높여야(B안의 Net을 깎아야) A와 같아짐
be_tc = data['tc_b'] + gap

# 3. 유불리 분석 및 메시지 구성
# 매입(Purchase)일 때: B안의 Net이 A안보다 작아야(gap < 0) 유리함 = 내가 돈을 적게 주니까
# 매출(Sales)일 때: B안의 Net이 A안보다 커야(gap > 0) 유리함 = 내가 돈을 많이 받으니까

if mode == "Purchase":
    is_favorable = net_b <= net_a  # 적게 지불할수록 유리
    diff_val = abs(gap)
    status_msg = f"✅ B안이 A안보다 <b>${diff_val:,.2f}</b> 적게 지불하므로 유리합니다." if is_favorable else \
                 f"❌ B안이 A안보다 <b>${diff_val:,.2f}</b> 더 많이 지불하므로 불리합니다."
else:  # Sales
    is_favorable = net_b >= net_a  # 많이 받을수록 유리
    diff_val = abs(gap)
    status_msg = f"✅ B안이 A안보다 <b>${diff_val:,.2f}</b> 더 많이 받으므로 유리합니다." if is_favorable else \
                 f"❌ B안이 A안보다 <b>${diff_val:,.2f}</b> 적게 받으므로 불리합니다."

status_color = "#27ae60" if is_favorable else "#e74c3c"
bg_color = "#f8fff9" if is_favorable else "#fff8f8"

# UI 출력 (HTML 부분은 동일, 변수만 매칭)
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 15px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">🎯 A안과 동일해지기 위한 B안의 목표 TC</p>
        <p style="margin: 5px 0; color: #2c3e50; font-size: 28px; font-weight: 800;">${be_tc:,.2f}</p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
    </div>
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {status_color};">
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 A안 대비 B안 분석</p>
        <p style="margin: 0; color: #34495e; font-size: 14px;">
            {status_msg}
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 7. 하단 이동 버튼 ---
st.markdown(f"""
    <a href="#link_to_top" style="text-decoration: none;">
        <div style="width: 100%; padding: 15px; background-color: #2e4053; color: white; border-radius: 10px; font-size: 16px; font-weight: bold; text-align: center; margin-top: 30px;">
            ⬆️ 최상단으로 돌아가기
        </div>
    </a>
""", unsafe_allow_html=True)
