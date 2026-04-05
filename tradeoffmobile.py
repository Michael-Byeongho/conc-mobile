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

# --- 6. 협상 타겟 계산 (TC Gap 분석) ---
st.markdown("---")
st.markdown("### 🎯 A안 대비 B안의 조건 차이 (TC 환산)")

# 1. B안에서 TC만 0으로 만들었을 때의 Net value를 구합니다. (순수 금속 조건 가치)
net_b_zero_tc = calc_unit_net(
    mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
    au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
    ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b']
)

# 2. A안의 최종 결과(TC가 포함된 기준점)와 비교합니다.
# A안과 B안의 조건이 똑같다면, (net_b_zero_tc - 30) - net_a = 0 이 됩니다.
# 여기서 구하고 싶은 것은 "B안의 조건이 A안보다 TC 기준 몇 불 이득인가?" 입니다.
tc_benefit = net_b_zero_tc - res['a']

# 3. 유불리 분석 (Gap 기준)
# tc_benefit이 0보다 크면 B안의 금속 조건이 A안보다 그만큼 유리하다는 뜻입니다.
is_favorable = tc_benefit >= -0.0001
status_color = "#27ae60" if is_favorable else "#e74c3c"
bg_color = "#f8fff9" if is_favorable else "#fff8f8"

st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 15px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">⚖️ A안 대비 B안의 조건 유리도 (TC 환산)</p>
        <p style="margin: 5px 0; color: {status_color}; font-size: 28px; font-weight: 800;">
            {'+' if tc_benefit > 0 else ''}{tc_benefit:,.2f} $/mt
        </p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
    </div>
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {status_color};">
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 분석 결과</p>
        <p style="margin: 0; color: #34495e; font-size: 14px;">
            {"✅ B안의 금속 정산 조건이 A안보다 유리하여, TC를 <b>$" + f"{abs(tc_benefit):,.2f}" + "</b> 더 많이 받아낼 수 있는 여유가 있습니다." if is_favorable else 
             "❌ B안의 금속 정산 조건이 A안보다 불리하여, A안과 맞추려면 TC를 <b>$" + f"{abs(tc_benefit):,.2f}" + "</b> 더 깎아야 합니다."}
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
