import streamlit as st
import pandas as pd

# --- 0. Config & Style (모바일 최적화 및 스타일 유지) ---
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
            padding: 5px 10px; 
            border-radius: 5px; 
            margin-bottom: 10px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic (PD/MD 분기 로직 반영) ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, 
                  au_p, au_a, au_py, au_rc, au_dt, au_dv, 
                  ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # 1. Cu Payable Content 계산
    # PD(Unit Deduct): (Assay - Deduct) * Pay%
    # MD(Percentage Deduct): Assay * (1 - Deduct%) * Pay%
    if cu_dt == "PD":
        cu_content = (cu_a - cu_dv) * (cu_py / 100.0)
    else: # MD
        cu_content = cu_a * (1 - cu_dv / 100.0) * (cu_py / 100.0)
    v_cu_pay = (max(0, cu_content) / 100.0) * (cu_p - (cu_rc / 100.0 * lb_to_mt))
    
    # 2. Ag Payable Content 계산
    if ag_dt == "PD":
        ag_content = (ag_a - ag_dv) * (ag_py / 100.0)
    else: # MD
        ag_content = ag_a * (1 - ag_dv / 100.0) * (ag_py / 100.0)
    v_ag_pay = (max(0, ag_content) * g_to_oz) * (ag_p - ag_rc)
    
    # 3. Au Payable Content 계산
    if au_dt == "PD":
        au_content = (au_a - au_dv) * (au_py / 100.0)
    else: # MD
        au_content = au_a * (1 - au_dv / 100.0) * (au_py / 100.0)
    v_au_pay = (max(0, au_content) * g_to_oz) * (au_p - au_rc)
    
    # Net 계산
    net = (v_cu_pay + v_ag_pay + v_au_pay) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 최상단 대시보드 레이아웃 ---
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

res_area = st.container()

# --- 3. 공통 변수 ---
with st.expander("⚙️ 시장 가격 및 품위 (공통)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0)
        ag_p = st.number_input("Ag Price ($/Oz)", value=30.0)
        au_p = st.number_input("Au Price ($/Oz)", value=2500.0)
    with c2:
        cu_a = st.number_input("Cu Assay (%)", value=25.0)
        ag_a = st.number_input("Ag Assay (g/DMT)", value=50.0)
        au_a = st.number_input("Au Assay (g/DMT)", value=1.0)

# --- 4. Main Inputs (A, B, C안 설정) ---
st.markdown("### ⚖️ 조건 세부 설정")
tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = [("A (Base)안", "a", 80.0), ("B안", "b", 80.0), ("C안", "c", 80.0)]
data = {}

for i, (name, k, def_tc) in enumerate(cases):
    with tabs[i]:
        # Cu Section
        st.markdown(f"<div class='section-head'>{name} - Copper Terms</div>", unsafe_allow_html=True)
        data[f"cu_py_{k}"] = st.number_input("Cu Pay (%)", value=100.0, key=f"cp_{k}")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1: data[f"cu_dt_{k}"] = st.radio("Cu deduct type", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
        with c_sub2: data[f"cu_dv_{k}"] = st.number_input("Cu Deduct Val (unit or %)", value=1.0, key=f"cdv_{k}")
        
        # Ag Section
        st.divider()
        st.markdown(f"**Silver (Ag) Terms**")
        data[f"ag_py_{k}"] = st.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
        c_sub3, c_sub4 = st.columns(2)
        with c_sub3: data[f"ag_dt_{k}"] = st.radio("Ag deduct type", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
        with c_sub4: data[f"ag_dv_{k}"] = st.number_input("Ag Deduct Val (g or %)", value=30.0, key=f"adv_{k}")

        # Au Section
        st.divider()
        st.markdown(f"**Gold (Au) Terms**")
        data[f"au_py_{k}"] = st.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
        c_sub5, c_sub6 = st.columns(2)
        with c_sub5: data[f"au_dt_{k}"] = st.radio("Au deduct type", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
        with c_sub6: data[f"au_dv_{k}"] = st.number_input("Au Deduct Val (g or %)", value=1.0, key=f"audv_{k}")
        
        # TC/RC Section
        st.markdown(f"<div class='section-head'>📉 Deductions (TC/RC)</div>", unsafe_allow_html=True)
        c_sub7, c_sub8 = st.columns(2)
        with c_sub7: 
            data[f"tc_{k}"] = st.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input("Cu RC (c/lb)", value=8.0, key=f"curc_{k}")
        with c_sub8:
            data[f"ag_rc_{k}"] = st.number_input("Ag RC ($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input("Au RC ($/oz)", value=5.0, key=f"aurc_{k}")

# --- 5. Calculation & Display ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with res_area:
    def get_delta_html(delta_val):
        if delta_val > 0:
            return f"<span style='color: #1e8449 !important; background-color: #e8f8f5 !important; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: clamp(10px, 3vw, 12px);'>↑ {delta_val:,.2f}</span>"
        elif delta_val < 0:
            return f"<span style='color: #c0392b !important; background-color: #fdedec !important; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: clamp(10px, 3vw, 12px);'>↓ {abs(delta_val):,.2f}</span>"
        return f"<span style='color: #7f8c8d !important; background-color: #f2f4f4 !important; padding: 2px 8px; border-radius: 6px; font-weight: bold; font-size: clamp(10px, 3vw, 12px);'>- 0.00</span>"

    d_b = res['b'] - res['a']
    d_c = res['c'] - res['a']

    st.markdown(f"""
        <style>
            .flex-container {{ display: flex; justify-content: space-between; gap: 8px; width: 100%; margin-bottom: 20px; }}
            .flex-card {{ flex: 1; background-color: #f8f9fa; padding: 10px 5px; border-radius: 8px; border-left: 4px solid #2e4053; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
            .card-title {{ color: #7f8c8d; font-size: clamp(10px, 2.8vw, 14px); margin-bottom: 4px; }}
            .card-value {{ color: #2c3e50; font-weight: 900; font-size: clamp(14px, 4.5vw, 22px); margin-bottom: 2px; }}
        </style>
        <div class="flex-container">
            <div class="flex-card">
                <div class="card-title">A안(원안)</div>
                <div class="card-value">${abs(res['a']):,.1f}/t</div>
                <div style='font-size: 11px; color: transparent;'>-</div>
            </div>
            <div class="flex-card">
                <div class="card-title">B안</div>
                <div class="card-value">${abs(res['b']):,.1f}/t</div>
                {get_delta_html(d_b)}
            </div>
            <div class="flex-card">
                <div class="card-title">C안</div>
                <div class="card-value">${abs(res['c']):,.1f}/t</div>
                {get_delta_html(d_c)}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. 협상 타겟 계산 (Break-even TC) ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

# TC가 0일 때의 B안 가치 계산 (Target TC 산출용)
val_b_no_tc = calc_unit_net(mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                            au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                            ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b'])

# Target TC: A안의 Net과 같아지게 만드는 B안의 TC 값
if mode == "Purchase (매입)":
    # 매입 시: Net = -(Value - TC) = TC - Value.  Target TC = A_Net + B_Value
    be_tc = res['a'] + abs(val_b_no_tc) 
    diff_tc = be_tc - data['tc_b']
    is_favorable = diff_tc <= 0 
else:
    # 매출 시: Net = Value - TC. Target TC = B_Value - A_Net
    be_tc = abs(val_b_no_tc) - res['a']
    diff_tc = data['tc_b'] - be_tc
    is_favorable = diff_tc >= 0

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
            {"✅ 현재 제안이 목표보다 <b>$"+f"{abs(diff_tc):,.2f}"+"</b> 우수합니다." if is_favorable else 
             "❌ 현재 제안이 목표보다 <b>$"+f"{abs(diff_tc):,.2f}"+"</b> 불리합니다."}
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
