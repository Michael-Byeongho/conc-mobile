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

# --- 1. Core Logic (은 20g = $45.01 차이 보장) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, 
                  au_p, au_a, au_py, au_rc, au_dt, au_dv, 
                  ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # Cu 가치 (Deduction이 시장가를 따르도록 수정)
    if cu_dt == "PD":
        cu_payable_content = (cu_a * (cu_py / 100.0)) - cu_dv
    else:
        cu_payable_content = cu_a * (cu_py / 100.0 - cu_dv / 100.0)
    v_cu_pay = (cu_payable_content / 100.0) * cu_p - (max(0, cu_payable_content) / 100.0) * (cu_rc * lb_to_mt)
    
    # Ag 가치 (20g PD 차이 = 정확히 $45.01)
    if ag_dt == "PD":
        ag_payable_content = (ag_a * (ag_py / 100.0)) - ag_dv
    else:
        ag_payable_content = ag_a * (ag_py / 100.0 - ag_dv / 100.0)
    v_ag_pay = (ag_payable_content * g_to_oz * ag_p) - (max(0, ag_payable_content) * g_to_oz * ag_rc)
    
    # Au 가치
    if au_dt == "PD":
        au_payable_content = (au_a * (au_py / 100.0)) - au_dv
    else:
        au_payable_content = au_a * (au_py / 100.0 - au_dv / 100.0)
    v_au_pay = (au_payable_content * g_to_oz * au_p) - (max(0, au_payable_content) * g_to_oz * au_rc)
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 상단 레이아웃 ---
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

# 최상단 결과 요약 공간 확보
res_placeholder = st.empty()

# --- 3. 입력 섹션 (공통 및 탭) ---
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

tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = [("A (Base)안", "a", 30.0), ("B안", "b", 30.0), ("C안", "c", 30.0)]
data = {}

for i, (name, k, def_tc) in enumerate(cases):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{name} - Metals Terms</div>", unsafe_allow_html=True)
        # Cu
        c_cu1, c_cu2, c_cu3 = st.columns(3)
        data[f"cu_py_{k}"] = c_cu1.number_input("Cu Pay (%)", value=100.0, key=f"cp_{k}")
        data[f"cu_dt_{k}"] = c_cu2.radio("Cu Deduct", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
        data[f"cu_dv_{k}"] = c_cu3.number_input("Cu PD/MD Val", value=1.25, key=f"cdv_{k}")
        # Ag
        st.divider()
        c_ag1, c_ag2, c_ag3 = st.columns(3)
        data[f"ag_py_{k}"] = c_ag1.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
        data[f"ag_dt_{k}"] = c_ag2.radio("Ag Deduct", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
        data[f"ag_dv_{k}"] = c_ag3.number_input("Ag PD/MD Val", value=50.0, key=f"adv_{k}")
        # Au
        st.divider()
        c_au1, c_au2, c_au3 = st.columns(3)
        data[f"au_py_{k}"] = c_au1.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
        data[f"au_dt_{k}"] = c_au2.radio("Au Deduct", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
        data[f"au_dv_{k}"] = c_au3.number_input("Au PD/MD Val", value=1.25, key=f"audv_{k}")
        # TC/RC
        st.markdown(f"<div class='section-head'>📉 TC/RC</div>", unsafe_allow_html=True)
        c_tr1, c_tr2 = st.columns(2)
        data[f"tc_{k}"] = c_tr1.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
        data[f"cu_rc_{k}"] = c_tr1.number_input("Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
        data[f"ag_rc_{k}"] = c_tr2.number_input("Ag RC ($/oz)", value=0.4, key=f"agrc_{k}")
        data[f"au_rc_{k}"] = c_tr2.number_input("Au RC ($/oz)", value=5.0, key=f"aurc_{k}")

# --- 4. Calculation (모든 입력 후 계산 수행) ---
res = {}
for _, k, _ in cases:
    res[k] = calc_unit_net(
        mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]
    )

# --- 5. 결과 출력 (Sidebar & Placeholder) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 최종 계산 결과")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    st.metric("B안 (vs A)", f"${abs(res['b']):,.2f} /t", f"{res['b'] - res['a']:,.2f}")
    st.metric("C안 (vs A)", f"${abs(res['c']):,.2f} /t", f"{res['c'] - res['a']:,.2f}")

d_b = res['b'] - res['a']
d_c = res['c'] - res['a']

with res_placeholder:
    st.markdown(f"""
        <div style="margin-top: 10px; margin-bottom: 20px;">
            <p style="font-weight: bold; margin-bottom: 5px;">📊 분석 결과 요약</p>
            <div style="display: flex; justify-content: space-between; gap: 10px;">
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">A안 (Base)</div>
                    <div style="font-size:20px; font-weight:bold;">${abs(res['a']):,.2f}</div>
                </div>
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">B안</div>
                    <div style="font-size:20px; font-weight:bold;">${abs(res['b']):,.2f}</div>
                    <div style="font-size:14px; font-weight:bold; color:{'green' if d_b > 0 else 'red'}">{'▲' if d_b > 0 else '▼'} {abs(d_b):,.2f}</div>
                </div>
                <div style="flex:1; background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center;">
                    <div style="font-size:12px; color:#7f8c8d;">C안</div>
                    <div style="font-size:20px; font-weight:bold;">${abs(res['c']):,.2f}</div>
                    <div style="font-size:14px; font-weight:bold; color:{'green' if d_c > 0 else 'red'}">{'▲' if d_c > 0 else '▼'} {abs(d_c):,.2f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. 협상 타겟 계산 (Target TC) ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

# B안의 조건하에서 TC가 0일 때의 순수 금속가치 (abs로 부호 고정)
val_b_pure = abs(calc_unit_net(mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                               au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                               ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b']))

# A안의 최종 Net(절댓값)과 동일해지기 위한 B안의 TC
# [매입] 금속가치(1000) - 목표지출(970) = 목표TC(30)
be_tc = val_b_pure - abs(res['a'])
diff_tc = be_tc - data['tc_b']
is_favorable = diff_tc >= -0.0001

status_color = "#27ae60" if is_favorable else "#e74c3c"
bg_color = "#f8fff9" if is_favorable else "#fff8f8"

st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 15px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">🎯 목표 TC (Target TC)</p>
        <p style="margin: 5px 0; color: #2c3e50; font-size: 28px; font-weight: 800;">${be_tc:,.2f}</p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
    </div>
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {status_color};">
        <p style="margin: 0; color: #34495e; font-size: 14px;">
            {f"✅ 현재 제안이 목표 대비 <b>${abs(diff_tc):,.2f}</b> 유리합니다." if is_favorable else 
             f"❌ 현재 제안이 목표 대비 <b>${abs(diff_tc):,.2f}</b> 불리합니다."}
        </p>
    </div>
""", unsafe_allow_html=True)
# --- 7. 하단 이동 버튼 ---
st.markdown("""
    <style>
        .top-link {
            display: block;
            width: 100%;
            padding: 15px;
            background-color: #2e4053;
            color: white !important;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 30px;
            text-decoration: none;
        }
        .top-link:hover { background-color: #3e5871; }
    </style>
    <a href="#top" class="top-link">
        ⬆️ 최상단으로 돌아가기
    </a>
""", unsafe_allow_html=True)
