import streamlit as st
st.markdown("<div id='link_to_top' name='link_to_top'></div>", unsafe_allow_html=True)

# --- 0. Config & Style ---
st.set_page_config(page_title="Copper Conc. Trade-off Tool", layout="centered")

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { background-color: white !important; color: #2c3e50 !important; }
        .stMarkdown, p, label { color: #2c3e50 !important; }
        .section-head { background-color: #2e4053; color: white !important; padding: 5px 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; font-size: 14px; }
        .metric-card { background:#f8f9fa; padding:15px; border-radius:8px; border-top:5px solid #2e4053; text-align:center; flex:1; }
    </style>
""", unsafe_allow_html=True)

# --- 1. 계산 함수 (구조 단순화) ---
def calculate_net_value(mode, tc, market, terms):
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # 1. Cu 가치
    if terms['cu_dt'] == "PD":
        cu_payable_unit = (market['cu_a'] * (terms['cu_py'] / 100.0)) - terms['cu_dv']
    else:
        cu_payable_unit = market['cu_a'] * (terms['cu_py'] - terms['cu_dv']) / 100.0
    v_cu = (max(0.0, cu_payable_unit) / 100.0) * (market['cu_p'] - (terms['cu_rc'] / 100.0 * lb_to_mt))

    # 2. Ag 가치
    if terms['ag_dt'] == "PD":
        ag_payable_oz = (market['ag_a'] * (terms['ag_py'] / 100.0) - terms['ag_dv']) * g_to_oz
    else:
        ag_payable_oz = market['ag_a'] * (terms['ag_py'] - terms['ag_dv']) / 100.0 * g_to_oz
    v_ag = max(0.0, ag_payable_oz) * (market['ag_p'] - terms['ag_rc'])

    # 3. Au 가치
    if terms['au_dt'] == "PD":
        au_payable_oz = (market['au_a'] * (terms['au_py'] / 100.0) - terms['au_dv']) * g_to_oz
    else:
        au_payable_oz = market['au_a'] * (terms['au_py'] - terms['au_dv']) / 100.0 * g_to_oz
    v_au = max(0.0, au_payable_oz) * (market['au_p'] - terms['au_rc'])
    net_value = v_cu + v_au + v_ag - tc
    return -net_value if "Purchase" in mode else net_value

# --- 2. UI 레이아웃 ---
st.title("⚡ 동정광 Trade-off 분석기")
mode = st.radio("🔄 거래 포지션 선택", ["Purchase (매입)", "Sales (매출)"], horizontal=True)
res_placeholder = st.empty()

# --- 3. 공통 입력 ---
with st.expander("⚙️ 시장 가격 및 품위 (공통)", expanded=True):
    c1, c2, c3 = st.columns(3)
    market = {
        "cu_p": c1.number_input("Cu Price ($/MT)", value=12000.0),
        "cu_a": c1.number_input("Cu Assay (%)", value=25.0),
        "ag_p": c2.number_input("Ag Price ($/Oz)", value=70.0),
        "ag_a": c2.number_input("Ag Assay (g/DMT)", value=350.0),
        "au_p": c3.number_input("Au Price ($/Oz)", value=4500.0),
        "au_a": c3.number_input("Au Assay (g/DMT)", value=5.0),
    }

# --- 4. 시나리오별 입력 ---
tabs = st.tabs(["A안 (Base)", "B안", "C안"])
res = {} # 결과 저장 딕셔너리 명칭을 res로 통일

for i, name in enumerate(["a", "b", "c"]):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{name.upper()}안 조건 설정</div>", unsafe_allow_html=True)
        col_tc, col_cu, col_au, col_ag = st.columns(4)
        
        with col_tc:
            tc = st.number_input(f"TC ($/DMT)", value=80.0, key=f"tc_{name}")
            cu_rc = st.number_input(f"Cu RC (c/lb)", value=8.0, key=f"curc_{name}")
            au_rc = st.number_input(f"Au RC ($/oz)", value=5.0, key=f"aurc_{name}")
            ag_rc = st.number_input(f"Ag RC ($/oz)", value=0.5, key=f"agrc_{name}")
        
        with col_cu:
            st.caption("Copper")
            cu_py = st.number_input("Pay (%)", value=96.5, key=f"cupy_{name}")
            cu_dt = st.radio("Deduct", ["PD", "MD"], key=f"cudt_{name}")
            cu_dv = st.number_input("Val", value=1.0, key=f"cudv_{name}")
        
        with col_ag:
            st.caption("Silver")
            ag_py = st.number_input("Pay (%)", value=90.0, key=f"agpy_{name}")
            ag_dt = st.radio("Deduct", ["PD", "MD"], index=1, key=f"agdt_{name}")
            ag_dv = st.number_input("Val", value=30.0, key=f"agdv_{name}")

        with col_au:
            st.caption("Gold")
            au_py = st.number_input("Pay (%)", value=90.0, key=f"aupy_{name}")
            au_dt = st.radio("Deduct", ["PD", "MD"], index=1, key=f"audt_{name}")
            au_dv = st.number_input("Val", value=1.0, key=f"audv_{name}")



        res[name] = calculate_net_value(mode, tc, market, {
            "cu_py": cu_py, "cu_dt": cu_dt, "cu_dv": cu_dv, "cu_rc": cu_rc,
            "au_py": au_py, "au_dt": au_dt, "au_dv": au_dv, "au_rc": au_rc,
            "ag_py": ag_py, "ag_dt": ag_dt, "ag_dv": ag_dv, "ag_rc": ag_rc
        })

# --- 5. 결과 분석 ---
d_b = res['b'] - res['a']
d_c = res['c'] - res['a']

with res_placeholder:
    st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
            <div class="metric-card">A안 (Base)<br><b>${abs(res['a']):,.2f}</b></div>
            <div class="metric-card">B안<br><b>${abs(res['b']):,.2f}</b><br><span style="color:{'#27ae60' if d_b > 0 else '#e74c3c'}">{'▲' if d_b > 0 else '▼'} {abs(d_b):,.2f}</span></div>
            <div class="metric-card">C안<br><b>${abs(res['c']):,.2f}</b><br><span style="color:{'#27ae60' if d_c > 0 else '#e74c3c'}">{'▲' if d_c > 0 else '▼'} {abs(d_c):,.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. 협상 타겟 계산 (TC Gap 분석) ---
st.markdown("---")
st.markdown("### 🎯 A안 대비 B안 비교 및 조정 목표 (Gap)")

# 1. 두 안의 Net 결과값 차이
net_diff = res['b'] - res['a']

# 2. Gap을 메꾸기 위한 TC 조정액 계산
if "Purchase" in mode:
    required_tc_adj = -net_diff
else:
    required_tc_adj = net_diff

# 3. 상태 판별 (유리 / 동일 / 불리)
if abs(net_diff) < 0.001:  # 동일한 경우
    status_type = "equal"
    status_color = "#95a5a6" # 회색
    bg_color = "#f4f6f7"
elif net_diff > 0:         # 유리한 경우
    status_type = "favorable"
    status_color = "#27ae60" # 녹색
    bg_color = "#f8fff9"
else:                      # 불리한 경우
    status_type = "unfavorable"
    status_color = "#e74c3c" # 붉은색
    bg_color = "#fff8f8"

# 4. 메시지 구성
if status_type == "equal":
    analysis_text = "✅ 현재 B안의 조건이 <b>A안과 완전히 동일합니다.</b>"
    guide_text = "추가적인 TC 조정 없이도 A안과 같은 수익성을 유지합니다."
elif status_type == "favorable":
    analysis_text = f"✅ B안의 금속 조건이 유리합니다. (A안 대비 <b>+${abs(net_diff):,.2f}</b>)"
    guide_text = f"A안과 수익을 맞추려면 톤당 <b>${abs(required_tc_adj):,.2f}</b> 만큼 " + ("낮춰줄(인하)" if "Purchase" in mode else "높여줄(인상)") + " 여유가 있습니다."
else:
    analysis_text = f"❌ B안의 금속 조건이 불리합니다. (A안 대비 <b>-${abs(net_diff):,.2f}</b>)"
    guide_text = f"A안과 수익을 맞추려면 톤당 <b>${abs(required_tc_adj):,.2f}</b> 만큼 " + ("더 받아야(인상)" if "Purchase" in mode else "더 깎아야(인하)") + " 합니다."

# 5. UI 출력
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 15px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">⚖️ A안 수준의 수익을 맞추기 위한 B안의 조정가능(필요)액</p>
        <p style="margin: 5px 0; color: {status_color}; font-size: 28px; font-weight: 800;">
            {'+' if required_tc_adj > 0.001 else ''}{required_tc_adj:,.2f} $/mt
        </p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
    </div>
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {status_color};">
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 분석 결과</p>
        <p style="margin: 0; color: #34495e; font-size: 14px;">
            {analysis_text}<br>
            <span style="font-size: 13px; color: #7f8c8d;">{guide_text}</span>
        </p>
    </div>
""", unsafe_allow_html=True)

#7. 상단이동
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
    <a href="#link_to_top" target="_self" class="top-link">
        ⬆️ 최상단으로 돌아가기
    </a>
""", unsafe_allow_html=True)
