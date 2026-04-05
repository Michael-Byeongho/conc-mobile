import streamlit as st

st.markdown("<div id='link_to_top' name='link_to_top'></div>", unsafe_allow_html=True)

# --- 0. 설정 ---
st.set_page_config(page_title="Trade-off Tool", layout="centered")

# --- 1. 계산 로직 (순서와 부호 완벽 정리) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, 
                  ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv, 
                  au_p, au_a, au_py, au_rc, au_dt, au_dv):
    
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # Cu 가치
    if cu_dt == "PD":
        cu_payable_ratio = (cu_a * (cu_py / 100.0) - cu_dv) / 100.0
    else:
        cu_payable_ratio = (cu_a * (cu_py - cu_dv) / 100.0) / 100.0
    v_cu = (cu_payable_ratio * cu_p) - (max(0.0, cu_payable_ratio) * (cu_rc / 100.0 * lb_to_mt))
    
    # Ag 가치 (20g 차이 시 약 $44.75 발생)
    if ag_dt == "PD":
        ag_payable_content = (ag_a * (ag_py / 100.0)) - ag_dv
    else:
        ag_payable_content = ag_a * (ag_py / 100.0 - ag_dv / 100.0)
    v_ag = max(0.0, ag_payable_content) * g_to_oz * (ag_p - ag_rc)
    
    # Au 가치
    if au_dt == "PD":
        au_payable_content = (au_a * (au_py / 100.0)) - au_dv
    else:
        au_payable_content = au_a * (au_py / 100.0 - au_dv / 100.0)
    v_au = max(0.0, au_payable_content) * g_to_oz * (au_p - au_rc)
    
    net_value = (v_cu + v_ag + v_au) - tc
    return -net_value if "Purchase" in mode else net_value

# --- 2. 상단 레이아웃 ---
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

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

# --- 3. 입력 탭 (이름 통일) ---
tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = ["a", "b", "c"]
res = {}

for i, k in enumerate(cases):
    with tabs[i]:
        st.subheader(f"{k.upper()}안 조건 설정")
        col1, col2, col3 = st.columns(3)
        # Cu
        cupy = col1.number_input(f"Cu Pay (%)", value=100.0, key=f"cupy_{k}")
        cudt = col2.radio(f"Cu Deduct", ["PD", "MD"], key=f"cudt_{k}")
        cudv = col3.number_input(f"Cu Val", value=1.25, key=f"cudv_{k}")
        # Ag
        st.divider()
        agpy = col1.number_input(f"Ag Pay (%)", value=90.0, key=f"agpy_{k}")
        agdt = col2.radio(f"Ag Deduct", ["PD", "MD"], key=f"agdt_{k}")
        agdv = col3.number_input(f"Ag Val", value=50.0, key=f"agdv_{k}")
        # Au
        st.divider()
        aupy = col1.number_input(f"Au Pay (%)", value=90.0, key=f"aupy_{k}")
        audt = col2.radio(f"Au Deduct", ["PD", "MD"], key=f"audt_{k}")
        audv = col3.number_input(f"Au Val", value=1.25, key=f"audv_{k}")
        # TC/RC
        st.divider()
        tc = col1.number_input(f"TC ($/DMT)", value=30.0, key=f"tc_{k}")
        curc = col2.number_input(f"Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
        agrc = col3.number_input(f"Ag RC ($/oz)", value=0.4, key=f"agrc_{k}")
        aurc = col1.number_input(f"Au RC ($/oz)", value=5.0, key=f"aurc_{k}")

        # 매 탭마다 즉시 계산해서 저장
        res[k] = calc_unit_net(mode, tc, cu_p, cu_a, cupy, curc, cudt, cudv, 
                               ag_p, ag_a, agpy, agrc, agdt, agdv, 
                               au_p, au_a, aupy, aurc, audt, audv)

# --- 4. 결과 사이드바 ---
with st.sidebar:
    st.header("📊 분석 결과")
    st.metric("A안 (Base)", f"${abs(res['a']):,.2f}")
    
    is_pur = "Purchase" in mode
    for k in ["b", "c"]:
        diff = res[k] - res['a']
        st.metric(f"{k.upper()}안 (vs A)", f"${abs(res[k]):,.2f}", f"{diff:,.2f}", 
                  delta_color="inverse" if is_pur else "normal")

st.info("**💡 확인:** Ag Val을 50에서 70으로 바꿔보세요. 약 $44.75가 정확히 변해야 합니다.")

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
