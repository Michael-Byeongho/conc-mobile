import streamlit as st
import pandas as pd

# --- 0. Config & Style (모바일 최적화) ---
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
            margin: 10px 0;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dv, au_p, au_a, au_py, au_rc, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dv):
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    # Payable 계산 (Deduction 방식 통합: dv값 자체가 PD/MD를 반영한 순수 공제후 품위라고 가정하거나 별도 로직 필요)
    # 여기서는 제공된 로직을 유지하되 변수 불일치만 수정함
    v_cu_pay = (cu_a * (cu_py / 100.0) / 100.0) * (cu_p - (cu_rc / 100.0 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py / 100.0) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py / 100.0) * g_to_oz) * (au_p - au_rc)
    
    # Unit Deductions
    d_cu = (cu_dv / 100.0) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 상단 UI ---
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)
st.title("⚡ 동정광 Trade off 분석")
mode = st.radio("🔄 거래 포지션", ["Purchase (매입)", "Sales (매출)"], horizontal=True)

# 결과가 표시될 컨테이너 미리 생성
res_area = st.container()

# --- 3. 공통 변수 ---
with st.expander("⚙️ 시장 가격 및 품위 (공통)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        cu_p = st.number_input("Cu Price ($/MT)", value=12000.0)
        ag_p = st.number_input("Ag Price ($/Oz)", value=30.0)
        au_p = st.number_input("Au Price ($/Oz)", value=2300.0)
    with c2:
        cu_a = st.number_input("Cu Assay (%)", value=25.0)
        ag_a = st.number_input("Ag Assay (g/DMT)", value=50.0)
        au_a = st.number_input("Au Assay (g/DMT)", value=1.0)

# --- 4. Main Inputs (탭 UI) ---
st.markdown("### ⚖️ 조건 세부 설정")
tabs = st.tabs(["A안(Base)", "B안", "C안"])
cases = [("A (Base)안", "a", 80.0), ("B안", "b", 85.0), ("C안", "c", 75.0)]
data = {}

for i, (name, k, def_tc) in enumerate(cases):
    with tabs[i]:
        st.markdown(f"<div class='section-head'>{name} Payable Metals</div>", unsafe_allow_html=True)
        data[f"cu_py_{k}"] = st.number_input("Cu Pay (%)", value=96.5, key=f"cp_{k}")
        c_sub1, c_sub2 = st.columns(2)
        with c_sub1: data[f"cu_dt_{k}"] = st.radio("Cu deduct", ["PD", "MD"], horizontal=True, key=f"cdt_{k}")
        with c_sub2: data[f"cu_dv_{k}"] = st.number_input("Cu PD/MD (%)", value=1.0, key=f"cdv_{k}")
        
        st.divider()
        data[f"ag_py_{k}"] = st.number_input("Ag Pay (%)", value=90.0, key=f"ap_{k}")
        c_sub3, c_sub4 = st.columns(2)
        with c_sub3: data[f"ag_dt_{k}"] = st.radio("Ag deduct", ["PD", "MD"], horizontal=True, key=f"adt_{k}")
        with c_sub4: data[f"ag_dv_{k}"] = st.number_input("Ag PD/MD(g)", value=30.0, key=f"adv_{k}")

        st.divider()
        data[f"au_py_{k}"] = st.number_input("Au Pay (%)", value=90.0, key=f"aup_{k}")
        c_sub5, c_sub6 = st.columns(2)
        with c_sub5: data[f"au_dt_{k}"] = st.radio("Au deduct", ["PD", "MD"], horizontal=True, key=f"audt_{k}")
        with c_sub6: data[f"au_dv_{k}"] = st.number_input("Au PD/MD(g)", value=1.0, key=f"audv_{k}")
        
        st.markdown(f"<div class='section-head'>📉 Deductions (TC/RC)</div>", unsafe_allow_html=True)
        c_sub7, c_sub8 = st.columns(2)
        with c_sub7: 
            data[f"tc_{k}"] = st.number_input("TC ($/DMT)", value=def_tc, key=f"tc_{k}")
            data[f"cu_rc_{k}"] = st.number_input("Cu RC(c/lb)", value=8.0, key=f"curc_{k}")
        with c_sub8:
            data[f"ag_rc_{k}"] = st.number_input("Ag RC($/oz)", value=0.5, key=f"agrc_{k}")
            data[f"au_rc_{k}"] = st.number_input("Au RC($/oz)", value=5.0, key=f"aurc_{k}")

# --- 5. Calculation (데이터 생성 후 계산) ---
res = {}
for k in ['a', 'b', 'c']:
    res[k] = calc_unit_net(
        mode, data[f"tc_{k}"], cu_p, cu_a, data[f"cu_py_{k}"], data[f"cu_rc_{k}"], data[f"cu_dv_{k}"],
        au_p, au_a, data[f"au_py_{k}"], data[f"au_rc_{k}"], data[f"au_dv_{k}"],
        ag_p, ag_a, data[f"ag_py_{k}"], data[f"ag_rc_{k}"], data[f"ag_dv_{k}"]
    )

d_b = res['b'] - res['a']
d_c = res['c'] - res['a']

# --- 6. 대시보드 출력 (색상 로직 강화) ---
with res_area:
    def get_delta_html(delta_val):
        # 양수일 때 (초록색)
        if delta_val > 0.01: 
            color = "#1e8449" # 진한 초록
            bg = "#e8f8f5"
            symbol = "▲"
        # 음수일 때 (빨간색)
        elif delta_val < -0.01:
            color = "#c0392b" # 진한 빨강
            bg = "#fdedec"
            symbol = "▼"
        # 변동 없을 때 (회색)
        else:
            color = "#7f8c8d"
            bg = "#f2f4f4"
            symbol = "-"
            
        return f"""
            <span style="
                color: {color} !important; 
                background-color: {bg} !important; 
                padding: 2px 8px; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 13px; 
                display: inline-block;
                margin-top: 4px;
            ">
                {symbol} {abs(delta_val):,.2f}
            </span>
        """

    st.markdown(f"""
        <style>
            .flex-container {{ display: flex; justify-content: space-between; gap: 10px; width: 100%; margin-bottom: 20px; }}
            .flex-card {{ 
                flex: 1; 
                background-color: #ffffff; 
                padding: 12px 5px; 
                border-radius: 10px; 
                border: 1px solid #e0e0e0;
                border-top: 4px solid #2e4053; 
                text-align: center; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .card-title {{ color: #7f8c8d !important; font-size: 13px; margin-bottom: 6px; font-weight: 600; }}
            .card-value {{ color: #2c3e50 !important; font-weight: 800; font-size: 19px; margin-bottom: 2px; }}
        </style>
        <div class="flex-container">
            <div class="flex-card">
                <div class="card-title">A안(원안)</div>
                <div class="card-value">${abs(res['a']):,.2f}</div>
                <div style="height: 25px;"></div> </div>
            <div class="flex-card">
                <div class="card-title">B안</div>
                <div class="card-value">${abs(res['b']):,.2f}</div>
                {get_delta_html(d_b)}
            </div>
            <div class="flex-card">
                <div class="card-title">C안</div>
                <div class="card-value">${abs(res['c']):,.2f}</div>
                {get_delta_html(d_c)}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. 대시보드 출력 (res_area 사용) ---
with res_area:
    def get_delta_html(delta_val):
        if delta_val > 0:
            return f"<span style='color: #1e8449 !important; background-color: #e8f8f5 !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 12px; display: inline-block;'>▲ {delta_val:,.2f}</span>"
        elif delta_val < 0:
            return f"<span style='color: #c0392b !important; background-color: #fdedec !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 12px; display: inline-block;'>▼ {abs(delta_val):,.2f}</span>"
        else:
            return f"<span style='color: #7f8c8d !important; background-color: #f2f4f4 !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 12px; display: inline-block;'>- 0.00</span>"

    st.markdown(f"""
        <style>
            .flex-container {{ display: flex; justify-content: space-between; gap: 8px; width: 100%; margin-bottom: 20px; }}
            .flex-card {{ flex: 1; background-color: #f8f9fa; padding: 10px 5px; border-radius: 8px; border-left: 4px solid #2e4053; text-align: center; }}
            .card-title {{ color: #7f8c8d; font-size: 13px; margin-bottom: 4px; }}
            .card-value {{ color: #2c3e50; font-weight: 900; font-size: 18px; margin-bottom: 5px; }}
        </style>
        <div class="flex-container">
            <div class="flex-card">
                <div class="card-title">A안(원안)</div>
                <div class="card-value">${abs(res['a']):,.2f}</div>
            </div>
            <div class="flex-card">
                <div class="card-title">B안</div>
                <div class="card-value">${abs(res['b']):,.2f}</div>
                {get_delta_html(d_b)}
            </div>
            <div class="flex-card">
                <div class="card-title">C안</div>
                <div class="card-value">${abs(res['c']):,.2f}</div>
                {get_delta_html(d_c)}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 7. 협상 타겟 계산 ---
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

# TC를 0으로 잡고 나머지 조건만으로 Net 계산
net_b_no_tc = calc_unit_net(mode, 0.0, cu_p, cu_a, data['cu_py_b'], data['cu_rc_b'], data['cu_dv_b'],
                            au_p, au_a, data['au_py_b'], data['au_rc_b'], data['au_dv_b'],
                            ag_p, ag_a, data['ag_py_b'], data['ag_rc_b'], data['ag_dv_b'])

# A안과 동일한 수익을 내기 위한 TC 산출
if mode == "Purchase (매입)":
    be_tc = res['a'] - net_b_no_tc
    diff_tc = be_tc - data['tc_b']
    is_favorable = diff_tc <= 0
else:
    be_tc = net_b_no_tc - res['a']
    diff_tc = data['tc_b'] - be_tc
    is_favorable = diff_tc >= 0

status_color = "#27ae60" if is_favorable else "#e74c3c"
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; text-align: center;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">🎯 목표 TC (Target TC)</p>
        <p style="margin: 5px 0; color: #2c3e50; font-size: 28px; font-weight: 800;">${abs(be_tc):,.2f}</p>
        <div style="height: 4px; background-color: {status_color}; width: 100%; border-radius: 2px;"></div>
        <p style="margin-top: 10px; font-size: 14px;">
            {"✅ 목표 대비 우위" if is_favorable else "❌ 목표 대비 열위"} 
            (차이: <b>${abs(diff_tc):,.2f}</b>)
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 7. 최상단 이동 버튼 (앵커 방식 - 색상 강제 고정) ---
st.markdown("""
    <a href="#link_to_top" style="text-decoration: none !important; color: white !important;">
        <div style="
            width: 100%; 
            padding: 15px; 
            background-color: #2e4053; 
            border-radius: 10px; 
            font-size: 16px; 
            font-weight: bold; 
            text-align: center;
            margin-top: 30px; 
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white !important;
        ">
            <span style="color: white !important;">⬆️ 최상단으로 돌아가기</span>
        </div>
    </a>
    <style>
        /* 링크 상태에 따른 모든 색상을 흰색으로 강제 고정 */
        a[href="#link_to_top"]:link, 
        a[href="#link_to_top"]:visited, 
        a[href="#link_to_top"]:hover, 
        a[href="#link_to_top"]:active {
            color: white !important;
            text-decoration: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
