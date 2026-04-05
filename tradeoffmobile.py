import streamlit as st
import pandas as pd

# --- 0. Config & Style (모바일 최적화) ---
st.set_page_config(page_title="Trade-off & Sensitivity Tool", layout="centered")

st.markdown("""
    <style>
        /* 기본 배경과 글자색 고정 (span에서 !important 제거) */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: #2c3e50 !important;
        }
        /* 라벨과 일반 텍스트는 검정색 유지 */
        .stMarkdown, p, label {
            color: #2c3e50 !important;
        }
        /* 세션 헤더 등 특정 요소 색상 */
        .section-head { background-color: #2e4053; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 1. Core Logic ---
def calc_unit_net(mode, tc, cu_p, cu_a, cu_py, cu_rc, cu_dt, cu_dv, au_p, au_a, au_py, au_rc, au_dt, au_dv, ag_p, ag_a, ag_py, ag_rc, ag_dt, ag_dv):
    g_to_oz = 1 / 31.1035
    lb_to_mt = 2204.62
    
    v_cu_pay = (cu_a * (cu_py / 100.0) / 100.0) * (cu_p - (cu_rc / 100.0 * lb_to_mt))
    v_ag_pay = (ag_a * (ag_py / 100.0) * g_to_oz) * (ag_p - ag_rc)
    v_au_pay = (au_a * (au_py / 100.0) * g_to_oz) * (au_p - au_rc)
    
    d_cu = (cu_dv / 100.0) * cu_p
    d_ag = (ag_dv * g_to_oz) * ag_p
    d_au = (au_dv * g_to_oz) * au_p
    
    net = (v_cu_pay + v_ag_pay + v_au_pay) - (d_cu + d_ag + d_au) - tc
    return -net if mode == "Purchase (매입)" else net

# --- 2. 최상단 대시보드 ---
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)
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
# --- 5. Calculation (수정된 부분) ---
with res_area:
    # 델타 포맷팅 함수 (색상 강제 적용 및 가시성 개선)
    def get_delta_html(delta_val):
        if delta_val > 0:
            # 양수일 때: 초록색 텍스트 (#1e8449)
            return f"<span style='color: #1e8449 !important; background-color: #e8f8f5 !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: clamp(10px, 3vw, 12px); display: inline-block;'>▲ {delta_val:,.2f}</span>"
        elif delta_val < 0:
            # 음수일 때: 붉은색 텍스트 (#c0392b)
            return f"<span style='color: #c0392b !important; background-color: #fdedec !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: clamp(10px, 3vw, 12px); display: inline-block;'>▼ {abs(delta_val):,.2f}</span>"
        else:
            # 변동 없을 때: 회색
            return f"<span style='color: #7f8c8d !important; background-color: #f2f4f4 !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: clamp(10px, 3vw, 12px); display: inline-block;'>- 0.00</span>"
    st.markdown(f"""
        <style>
            .flex-container {{
                display: flex;
                justify-content: space-between;
                gap: 8px;
                width: 100%;
                margin-bottom: 20px;
            }}
            .flex-card {{
                flex: 1;
                background-color: #f8f9fa;
                padding: 10px 5px;
                border-radius: 8px;
                border-left: 4px solid #2e4053;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                text-align: center;
                min-width: 0; /* flexbox 내 텍스트 잘림 방지 */
            }}
            .card-title {{
                color: #7f8c8d !important;
                font-size: clamp(10px, 2.8vw, 14px);
                margin-bottom: 4px;
                white-space: nowrap;
            }}
            .card-value {{
                color: #2c3e50 !important;
                font-weight: 900;
                font-size: clamp(14px, 4.5vw, 22px);
                margin-bottom: 5px;
                letter-spacing: -0.5px;
            }}
        </style>

        <div class="flex-container">
            <div class="flex-card">
                <div class="card-title">A안(원안)</div>
                <div class="card-value">${abs(res['a']):,.0f}</div>
                <div style='font-size: clamp(10px, 3vw, 13px); color: transparent;'>-</div>
            </div>
            <div class="flex-card">
                <div class="card-title">B안</div>
                <div class="card-value">${abs(res['b']):,.0f}</div>
                {get_delta_html(d_b)}
            </div>
            <div class="flex-card">
                <div class="card-title">C안</div>
                <div class="card-value">${abs(res['c']):,.0f}</div>
                {get_delta_html(d_c)}
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- 6. 협상 타겟 계산 ---
st.markdown("---")
st.markdown("### 🎯 협상 목표 계산 (A vs B)")

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
        <p style="margin: 0 0 5px 0; color: #2c3e50; font-size: 14px; font-weight: bold;">📊 B안 현재 제안 분석</p>
        <p style="margin: 0; color: #34495e; font-size: 14px; line-height: 1.5;">
            {"❌ 목표보다 <b><span style='color:"+status_color+"'>$"+str(round(abs(diff_tc),2))+"</span></b> 부족합니다." if not is_favorable else
             "✅ 목표보다 <b><span style='color:"+status_color+"'>$"+str(round(abs(diff_tc),2))+"</span></b> 더 받아냈습니다."}
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 7. 최상단 이동 버튼 (앵커 방식) ---
st.markdown("""
    <a href="#link_to_top" style="text-decoration: none;">
        <div style="
            width: 100%; 
            padding: 15px; 
            background-color: #2e4053; 
            color: white; 
            border-radius: 10px; 
            font-size: 16px; 
            font-weight: bold; 
            text-align: center;
            margin-top: 30px; 
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            ⬆️ 최상단으로 돌아가기
        </div>
    </a>
    """, unsafe_allow_html=True)

