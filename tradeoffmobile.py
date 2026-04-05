import streamlit as st
import pandas as pd

# --- 0. Config & Style (모바일 최적화) ---
# 기존 코드를 덮어쓸 때 이 설정이 파일 최상단에 "단 한 번만" 있어야 합니다.
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="centered")

st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { background-color: white !important; color: #2c3e50 !important; }
        .stMarkdown, p, span, label { color: #2c3e50 !important; }
        .stNumberInput input, .stSelectbox div { color: #2c3e50 !important; }
        button[data-baseweb="tab"] { font-size: 16px !important; font-weight: bold; }
        [data-testid="stMetric"] { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #2e4053; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .section-head { background-color: #2e4053; color: white; padding: 6px 12px; border-radius: 6px; font-size: 14px; margin: 15px 0 10px 0; font-weight: bold; text-align: center; }
        .md-hint { font-size: 12px; color: #d35400; font-weight: bold; margin-top: 2px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, au_p, au_a, au_py, au_rc, au_dt, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # 계산식 들여쓰기 4칸 통일
    v_cu_pay = (cu_a * (cu_py / 100.0) / 100.0) * (cu_p - (cu_rc / 100.0 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py / 100.0) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py / 100.0) * g_to_oz) * (au_p - au_rc)
    
    d_cu = (cu_dv / 100.0) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 최상단 대시보드 ---
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

res_area = st.container()

# --- 3. 공통 변수 ---
with st.expander("⚙️ 시장 가격 및 품위 (공통)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0)
        ag_p = st.number_input("Ag Price ($/Oz)", value=70.0)
        au_p = st.number_input("Au Price ($/Oz)", value=4500.0)
    with c2:
        cu_a = st.number_input("Cu Assay (%)", value=25.0)
        ag_a = st.number_input("Ag Assay (g/DMT)", value=50.0)
        au_a = st.number_input("Au Assay (g/DMT)", value=10.0)

# --- 4. Main Inputs (탭 UI) ---
st.markdown("### ⚖️ 조건 세부 설정")
tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = [("A (Base)안", "a", 80.0), ("B안", "b", 80.0), ("C안", "c", 80.0)]
data = {}

for i, (name, k, def_tc) in enumerate(cases):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{name} Payable Metals</div>", unsafe_allow_html=True)
        
        data[f"cu_py_{k}"] = st.number_input("Cu Pay (%)", value=100.0, key=f"cp_{k}")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1: data[f"cu_dt_{k}"] = st.radio("Cu deduct", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
        with c_sub2: data[f"cu_dv_{k}"] = st.number_input("Cu PD/MD (%)", value=1.0, key=f"cdv_{k}")
        
        if data[f"cu_py_{k}"] != 100.0:
            be_cu = abs(data[f"cu_dv_{k}"] / (1.0 - data[f"cu_py_{k}"] / 100.0))
            st.markdown(f"<p class='md-hint'>💡 MD 분기점: Cu {be_cu:.2f}%</p>", unsafe_allow_html=True)
        
        st.divider()
        
        data[f"ag_py_{k}"] = st.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
        c_sub3, c_sub4 = st.columns(2)
        with c_sub3: data[f"ag_dt_{k}"] = st.radio("Ag deduct", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
        with c_sub4: data[f"ag_dv_{k}"] = st.number_input("Ag PD/MD(g)", value=30.0, key=f"adv_{k}")
        
        if data[f"ag_py_{k}"] != 100.0:
            be_ag = abs(data[f"ag_dv_{k}"] / (1.0 - data[f"ag_py_{k}"] / 100.0))
            st.markdown(f"<p class='md-hint'>💡 MD 분기점: Ag {be_ag:.1f}g</p>", unsafe_allow_html=True)

        st.divider()

        data[f"au_py_{k}"] = st.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
        c_sub5, c_sub6 = st.columns(2)
        with c_sub5: data[f"au_dt_{k}"] = st.radio("Au deduct", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
        with c_sub6: data[f"au_dv_{k}"] = st.number_input("Au PD/MD(g)", value=1.0, key=f"audv_{k}")
        
        if data[f"au_py_{k}"] != 100.0:
            be_au = abs(data[f"au_dv_{k}"] / (1.0 - data[f"au_py_{k}"] / 100.0))
            st.markdown(f"<p class='md-hint'>💡 MD 분기점: Au {be_au:.1f}g</p>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='section-head'>📉 Deductions (TC/RC)</div>", unsafe_allow_html=True)
        c_sub7, c_sub8 = st.columns(2)
        with c_sub7: 
            data[f"tc_{k}"] = st.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input("Cu RC(c/lb)", value=8.0, key=f"curc_{k}")
        with c_sub8:
            data[f"ag_rc_{k}"] = st.number_input("Ag RC($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input("Au RC($/oz)", value=5.0, key=f"aurc_{k}")

# --- 5. Calculation ---
res = {k: calc_unit_net(mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dt_{k}"], data[f"cu_dv_{k}"],
                        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dt_{k}"], data[f"au_dv_{k}"],
                        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dt_{k}"], data[f"ag_dv_{k}"]) for _, k, _ in cases}

with res_area:
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("A안(기존,Base)", f"${abs(res['a']):,.0f}/t")
    with m2: st.metric("B안", f"${abs(res['b']):,.0f}/t", f"{res['b'] - res['a']:,.2f}")
    with m3: st.metric("C안", f"${abs(res['c']):,.0f}/t", f"{res['c'] - res['a']:,.2f}")

# --- 6. 협상 타겟 계산 ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산기(payable vs TC/ AvsB)")

net_b_no_tc = calc_unit_net(mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dt_b'], data['cu_dv_b'],
                            au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dt_b'], data['au_dv_b'],
                            ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dt_b'], data['ag_dv_b'])

if mode == "Purchase (매입)":
    be_tc = res['a'] - net_b_no_tc
    diff_tc = be_tc - data['tc_b']
    is_favorable = diff_tc <= 0
else:
    be_tc = net_b_no_tc - res['a']
    diff_tc = data['tc_b'] - be_tc
    is_favorable = diff_tc >= 0

status_color = "#27ae60" if is_favorable else "#e74c3c"
bg_color = "#f8fff9" if is_favorable else "#fff8f8"
border_color = "#2ecc71" if is_favorable else "#ff7675"

st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 15px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">🎯 목표 TC (Target TC)</p>
        <p style="margin: 5px 0; color: #2c3e50; font-size: 28px; font-weight: 800;">${be_tc:,.2f}</p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
    </div>
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color};">
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 B안 현재 제안(${data['tc_b']:.2f}) 분석</p>
        <p style="margin: 0; color: #34495e; font-size: 14px; line-height: 1.5;">
            {f"❌ 목표보다 <b><span style='color:{status_color}'>${abs(diff_tc):,.2f}</span></b> 부족합니다." if not is_favorable else
             f"✅ 목표보다 <b><span style='color:{status_color}'>${abs(diff_tc):,.2f}</span></b> 더 받아냈습니다."}
        </p>
    </div>
""", unsafe_allow_html=True)
