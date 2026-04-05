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

# --- 1. 최상단 앵커 설정 (48라인 근처) ---
st.markdown('<div id="top"></div>', unsafe_allow_html=True)

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

# --- 4. Calculation (모든 안의 최종 Net 계산) ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

# --- 5. 결과 출력 (Sidebar & Top Dashboard) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 최종 계산 결과")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    st.metric("B안 톤당이익 (vs A)", f"${abs(res['b']):,.2f} /t", f"{res['b'] - res['a']:,.2f}")
    st.metric("C안 톤당이익 (vs A)", f"${abs(res['c']):,.2f} /t", f"{res['c'] - res['a']:,.2f}")

# (이전에 만든 최상단 res_placeholder에 결과 채우기)
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

# --- 6. 협상 타겟 계산 (Break-even TC) ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

# B안의 순수 금속 가치 (TC 0일 때)
val_b_pure = abs(calc_unit_net(mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                               au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                               ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b']))

# A안의 최종 Net을 맞추기 위한 Target TC
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
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 B안 제안 분석</p>
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
