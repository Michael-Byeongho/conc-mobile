import streamlit as st
import pandas as pd

# --- 0. Config & Style (모바일 최적화 및 색상 고정) ---
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="centered")

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: #2c3e50 !important;
        }
        .stMarkdown, p, label {
            color: #2c3e50 !important;
        }
        .section-head { 
            background-color: #2e4053; 
            color: white !important; 
            padding: 8px 12px; 
            border-radius: 5px; 
            margin: 15px 0 10px 0;
            font-weight: bold;
            font-size: 14px;
        }
        /* 링크 및 버튼 텍스트 색상 강제 유지 */
        a { text-decoration: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic (수익 계산 함수) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dv, au_p, au_a, au_py, au_rc, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dv):
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # Payable Metals Value
    v_cu_pay = (cu_a * (cu_py / 100.0) / 100.0) * (cu_p - (cu_rc / 100.0 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py / 100.0) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py / 100.0) * g_to_oz) * (au_p - au_rc)
    
    # Unit Deductions (공제 품위 가치)
    d_cu = (cu_dv / 100.0) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    
    # Purchase(매입)일 경우 지출액이므로 (-)로 반환, Sales(매출)일 경우 수익이므로 (+) 반환
    # 차이 계산 시 '값이 클수록(더 양수일수록)' 유리하도록 설정
    return -net if mode == "Purchase (매입)" else net

# --- 2. 상단 UI 설정 ---
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)
st.title("⚡ 동정광 Trade-off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

# ⚠️ 실시간 대시보드가 표시될 예약 공간
dashboard_placeholder = st.empty()

# --- 3. 공통 변수 입력 (시장가 및 품위) ---
with st.expander("⚙️ 시장 가격 및 품위 (공통 설정)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0, step=100.0)
        ag_p = st.number_input("Ag Price ($/Oz)", value=30.0, step=1.0)
        au_p = st.number_input("Au Price ($/Oz)", value=2300.0, step=10.0)
    with c2:
        cu_a = st.number_input("Cu Assay (%)", value=25.0, step=0.1)
        ag_a = st.number_input("Ag Assay (g/DMT)", value=50.0, step=1.0)
        au_a = st.number_input("Au Assay (g/DMT)", value=1.0, step=0.1)

# --- 4. 세부 조건 설정 (탭 UI) ---
st.markdown("### ⚖️ 안별 세부 조건 설정")
tabs = st.tabs(["A안(Base)", "B안", "C안"])
case_keys = ["a", "b", "c"]
data = {}

for i, k in enumerate(case_keys):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{k.upper()}안 Payable & Deduction</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            data[f"cu_py_{k}"] = st.number_input(f"Cu Pay (%)", 96.5, key=f"cp_{k}")
            data[f"ag_py_{k}"] = st.number_input(f"Ag Pay (%)", 90.0, key=f"ap_{k}")
            data[f"au_py_{k}"] = st.number_input(f"Au Pay (%)", 90.0, key=f"aup_{k}")
        with col2:
            data[f"cu_dv_{k}"] = st.number_input(f"Cu PD/MD (%)", 1.0, key=f"cdv_{k}")
            data[f"ag_dv_{k}"] = st.number_input(f"Ag PD/MD (g)", 30.0, key=f"adv_{k}")
            data[f"au_dv_{k}"] = st.number_input(f"Au PD/MD (g)", 1.0, key=f"audv_{k}")
            
        st.markdown(f"<div class='section-head'>{k.upper()}안 TC/RC 설정</div>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            data[f"tc_{k}"] = st.number_input(f"TC ($/DMT)", 80.0 + (i*5), key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input(f"Cu RC (c/lb)", 8.0, key=f"curc_{k}")
        with col4:
            data[f"ag_rc_{k}"] = st.number_input(f"Ag RC ($/oz)", 0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input(f"Au RC ($/oz)", 5.0, key=f"aurc_{k}")

# --- 5. 계산 실행 ---
res = {}
for k in case_keys:
    res[k] = calc_unit_net(
        mode, data[f"tc_{k}"], cu_p, cu_a, 
        data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dv_{k}"],
        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dv_{k}"],
        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dv_{k}"]
    )

# A안 대비 차이 계산
d_b = res['b'] - res['a']
d_c = res['c'] - res['a']

# --- 6. 대시보드 렌더링 (Placeholder 업데이트) ---
def get_delta_tag(val):
    # 수익 개선(이득)일 때 초록색, 손실일 때 빨간색
    if val > 0.01:
        color, bg, symbol = "#1e8449", "#e8f8f5", "▲"
    elif val < -0.01:
        color, bg, symbol = "#c0392b", "#fdedec", "▼"
    else:
        color, bg, symbol = "#7f8c8d", "#f2f4f4", "-"
    return f"""
        <span style="color:{color} !important; background:{bg} !important; padding:2px 8px; 
        border-radius:4px; font-weight:bold; font-size:13px; display:inline-block; margin-top:5px;">
            {symbol} {abs(val):,.2f}
        </span>
    """

dashboard_placeholder.markdown(f"""
    <div style="display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px;">
        <div style="flex:1; background:#ffffff; padding:15px 5px; border-radius:10px; border:1px solid #e0e0e0; border-top:4px solid #2e4053; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <div style="color:#7f8c8d; font-size:12px; font-weight:600; margin-bottom:5px;">A안(원안)</div>
            <div style="color:#2c3e50; font-weight:800; font-size:20px;">${abs(res['a']):,.2f}</div>
            <div style="height:25px;"></div>
        </div>
        <div style="flex:1; background:#ffffff; padding:15px 5px; border-radius:10px; border:1px solid #e0e0e0; border-top:4px solid #2e4053; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <div style="color:#7f8c8d; font-size:12px; font-weight:600; margin-bottom:5px;">B안</div>
            <div style="color:#2c3e50; font-weight:800; font-size:20px;">${abs(res['b']):,.2f}</div>
            {get_delta_tag(d_b)}
        </div>
        <div style="flex:1; background:#ffffff; padding:15px 5px; border-radius:10px; border:1px solid #e0e0e0; border-top:4px solid #2e4053; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <div style="color:#7f8c8d; font-size:12px; font-weight:600; margin-bottom:5px;">C안</div>
            <div style="color:#2c3e50; font-weight:800; font-size:20px;">${abs(res['c']):,.2f}</div>
            {get_delta_tag(d_c)}
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 7. 협상 타겟 계산 섹션 ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 분석 (A vs B)")

# B안의 조건에서 TC만 0으로 설정했을 때의 가치 계산
val_b_no_tc = calc_unit_net(mode, 0.0, cu_p, cu_a, 
                            data['cu_py_b'], data['cu_rc_b'], data['cu_dv_b'],
                            au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dv_b'],
                            ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dv_b'])

# A안과 동일한 수익을 맞추기 위한 목표 TC 계산
if mode == "Purchase (매입)":
    target_tc = res['a'] - val_b_no_tc 
    diff_target = target_tc - data['tc_b']
    is_good = diff_target <= 0
else:
    target_tc = val_b_no_tc - res['a']
    diff_target = data['tc_b'] - target_tc
    is_good = diff_target >= 0

status_color = "#27ae60" if is_good else "#e74c3c"
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; text-align: center;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px; font-weight: 600;">🎯 목표 TC (Target TC)</p>
        <p style="margin: 10px 0; color: #2c3e50; font-size: 32px; font-weight: 900;">${abs(target_tc):,.2f}</p>
        <div style="height: 6px; background-color: {status_color}; width: 100%; border-radius: 3px; margin-bottom: 15px;"></div>
        <p style="margin: 0; font-size: 15px; color: #34495e;">
            현재 B안은 목표 대비 <b><span style="color:{status_color};">${abs(diff_target):,.2f}</span></b> 
            {"우위에 있습니다. ✅" if is_good else "열위에 있습니다. ❌"}
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 8. 최상단 이동 버튼 (색상 강제 고정 버전) ---
st.markdown("""
    <div style="margin-top: 40px; margin-bottom: 30px;">
        <a href="#link_to_top">
            <div style="width: 100%; padding: 16px; background-color: #2e4053; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <span style="color: white !important; font-weight: bold; font-size: 16px;">⬆️ 최상단으로 돌아가기</span>
            </div>
        </a>
    </div>
    <style>
        /* 모든 링크 상태에서 흰색 유지 */
        a:link, a:visited, a:hover, a:active { 
            color: white !important; 
            text-decoration: none !important; 
        }
    </style>
""", unsafe_allow_html=True)
