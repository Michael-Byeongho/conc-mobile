
import streamlit as st
st.markdown("<div id='link_to_top' name='link_to_top'></div>", unsafe_allow_html=True)

# --- 0. Config ---
st.set_page_config(page_title="Trade-off Tool", layout="centered")

# --- 1. Core Logic (수정됨: 모든 금속 RC 절감 로직 적용) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, 
                  au_p, au_a, au_py, au_rc, au_dt, au_dv, 
                  ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # 1. Cu 가치
    if cu_dt == "PD":
        cu_payable_ratio = (cu_a * (cu_py / 100.0) - cu_dv) / 100.0
    else:
        cu_payable_ratio = (cu_a * (cu_py - cu_dv) / 100.0) / 100.0
    v_cu = (cu_payable_ratio * cu_p) - (max(0.0, cu_payable_ratio) * (cu_rc / 100.0 * lb_to_mt))
    
    # 2. Ag 가치 (PD 20g 변경 시 약 $44.75 차이 발생)
    if ag_dt == "PD":
        ag_payable_content = (ag_a * (ag_py / 100.0)) - ag_dv
    else:
        ag_payable_content = ag_a * (ag_py / 100.0 - ag_dv / 100.0)
    v_ag = max(0.0, ag_payable_content) * g_to_oz * (ag_p - ag_rc)
    
    # 3. Au 가치
    if au_dt == "PD":
        au_payable_content = (au_a * (au_py / 100.0)) - au_dv
    else:
        au_payable_content = au_a * (au_py / 100.0 - au_dv / 100.0)
    v_au = max(0.0, au_payable_content) * g_to_oz * (au_p - au_rc)
    
    net_value = (v_cu + v_ag + v_au) - tc

    if "Purchase" in mode:
        return -net_value
    else:
        return net_value

# --- 2. 상단 레이아웃 ---
st.title("⚡ 동정광 Trade off 분석")
st.info("**📢 공지사항:** 본 계산기는 **DMT 1톤** 기준이며, 실질적인 RC 절감 효과를 반영합니다.")

mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)
res_placeholder = st.empty()

# --- 3. 입력 섹션 (Key값 전면 수정 및 통일) ---
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
        st.markdown(f"**{name} - Metals Terms**")
        # Cu
        c_cu1, c_cu2, c_cu3 = st.columns(3)
        data[f"cu_py_{k}"] = c_cu1.number_input("Cu Pay (%)", value=100.0, key=f"cu_py_{k}")
        data[f"cu_dt_{k}"] = c_cu2.radio("Cu Deduct", ["PD", "MD"], horizontal=True, key=f"cu_dt_{k}")
        data[f"cu_dv_{k}"] = c_cu3.number_input("Cu PD/MD Val", value=1.25, key=f"cu_dv_{k}")
        
        # Ag
        st.divider()
        c_ag1, c_ag2, c_ag3 = st.columns(3)
        data[f"ag_py_{k}"] = c_ag1.number_input("Ag Pay (%)", value=90.0, key=f"ag_py_{k}")
        data[f"ag_dt_{k}"] = c_ag2.radio("Ag Deduct", ["PD", "MD"], horizontal=True, key=f"ag_dt_{k}")
        data[f"ag_dv_{k}"] = c_ag3.number_input("Ag PD/MD Val", value=50.0, key=f"ag_dv_{k}")
        
        # Au
        st.divider()
        c_au1, c_au2, c_au3 = st.columns(3)
        data[f"au_py_{k}"] = c_au1.number_input("Au Pay (%)", value=90.0, key=f"au_py_{k}")
        data[f"au_dt_{k}"] = c_au2.radio("Au Deduct", ["PD", "MD"], horizontal=True, key=f"au_dt_{k}")
        data[f"au_dv_{k}"] = c_au3.number_input("Au PD/MD Val", value=1.25, key=f"au_dv_{k}")
        
        # TC/RC (Key 불일치 해결: 호출부와 동일하게 맞춤)
        st.divider()
        c_tr1, c_tr2 = st.columns(2)
        data[f"tc_{k}"] = c_tr1.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
        data[f"cu_rc_{k}"] = c_tr1.number_input("Cu RC (c/lb)", value=8.0, key=f"cu_rc_{k}")
        data[f"ag_rc_{k}"] = c_tr2.number_input("Ag RC ($/oz)", value=0.4, key=f"ag_rc_{k}")
        data[f"au_rc_{k}"] = c_tr2.number_input("Au RC ($/oz)", value=5.0, key=f"au_rc_{k}")

# --- 4. Calculation ---
res = {}
for _, k, _ in cases:
    res[k] = calc_unit_net(
        mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]
    )

# --- 5. 결과 출력 (Sidebar) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("📊 최종 계산 결과")
    st.metric("A (비교기준값)", f"${abs(res['a']):,.2f} /t")
    
    d_b = res['b'] - res['a']
    d_c = res['c'] - res['a']
    is_purchase = "Purchase" in mode
    
    st.metric("B안 (vs A)", f"${abs(res['b']):,.2f} /t", f"{d_b:,.2f}", delta_color="inverse" if is_purchase else "normal")
    st.metric("C안 (vs A)", f"${abs(res['c']):,.2f} /t", f"{d_c:,.2f}", delta_color="inverse" if is_purchase else "normal")

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
