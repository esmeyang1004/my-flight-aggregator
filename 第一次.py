import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime, timedelta
from streamlit_echarts import st_echarts

# 1. 資料庫初始化
DB_FILE = 'my_premium_stable_flight_data.csv'
columns_list = ["去程日期", "回程日期", "去/回程航線", "航空公司", "航班代號", "航班時間", "人數", "單人總票價(來回)", "總花費", "可購買網站"]

def init_csv():
    df_init = pd.DataFrame(columns=columns_list)
    df_init.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

if not os.path.exists(DB_FILE):
    init_csv()

# 設定網頁標題
st.set_page_config(layout="wide", page_title="MyPlaneTicket")

# ==================== 💎 經典版 CSS 樣式表 ====================
st.markdown("""
    <style>
        .stApp {
            background-color: #0F172A;
            color: #E2E8F0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        h1, h2, h3, h4, p, span, label {
            color: #F8FAFC !important;
        }
        .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
        
        /* 搜尋按鈕（啟用狀態） */
        div.stButton > button:first-child:not([disabled]) {
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        
        /* 防呆禁用狀態 */
        div.stButton > button:first-child:disabled {
            background-color: #1E293B !important;
            color: #475569 !important;
            border: 1px solid #334155 !important;
        }
        
        /* 表格工具列 */
        div[data-testid="stDataFrameToolbar"] {
            background-color: #1E293B !important;
            border: 1px solid #475569 !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==================== 🪐 網頁標題區 ====================
st.markdown("""
    <div style='margin-bottom: 35px; border-left: 4px solid #3B82F6; padding-left: 15px;'>
        <h1 style='margin: 0; font-size: 32px; font-weight: 800; letter-spacing: -0.5px;'>MY PLANE TICKET</h1>
        <p style='margin: 5px 0 0 0; color: #94A3B8; font-size: 14px; letter-spacing: 0.5px;'>GDS-GRADE MULTI-FLIGHT AGGREGATOR ENGINE</p>
    </div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([1, 2], gap="large")

# ==================== 📝 左側：搜尋表單 ＋ 【新增：動態姓名輸入格子】 ====================
with left_col:
    st.markdown("### Round-Trip Search Center")
    st.write("---")
    
    # 🌟 升級點：新增使用者姓名輸入框，預設叫「旅客」，使用者填什麼，右邊大腦就叫他什麼！
    user_name = st.text_input("使用者姓名 User Name", value="Esme").strip()
    if not user_name:
        user_name = "旅客" # 防呆機制：如果使用者手殘把格子全刪光，預設回歸旅客
        
    form_valid = True
    today = datetime.now()
    dep_date = st.date_input("去程日期 Departure Date", today)
    ret_date = st.date_input("回程日期 Return Date", today + timedelta(days=7))
    
    dep_airport = st.text_input("出發地 Airport (Origin)", placeholder="例如：TPE").upper().strip()
    if not dep_airport: form_valid = False
        
    arr_airport = st.text_input("目的地 Airport (Destination)", placeholder="例如：NRT").upper().strip()
    if not arr_airport: form_valid = False
        
    pax = st.number_input("搭乘人數 Passengers", min_value=1, value=1, step=1)
    
    st.markdown("##### 隱藏成本與附加服務換算")
    add_tax = st.checkbox("加計海外刷卡手續費 (1.5%)")
    add_luggage = st.checkbox("需要加購託運行李重量？")
    st.caption("💡 智慧比價提示：傳統航空皆已免費內含行李額度；若勾選此項，系統會自動幫廉航（台灣虎航）補上行李加購費進行公平比價。")
    
    st.write("")
    if dep_airport and arr_airport:
        if ret_date < dep_date:
            st.error("警告：回程日期不能早於去程日期！")
            form_valid = False
        else:
            st.write("智慧拆單引擎就緒：將為您交叉配對跨航空最佳解")
    else:
        st.write("等待輸入航線資訊解鎖按鈕...")
        
    st.write("")
    save_btn = st.button("FETCH ALL SCHEDULED FLIGHTS", use_container_width=True, disabled=not form_valid)
    
    # 后台交叉比价大脑
    if save_btn and form_valid:
        collected_rows = []
        dep_date_str = dep_date.strftime('%Y-%m-%d')
        ret_date_str = ret_date.strftime('%Y-%m-%d')
        route_display = f"{dep_airport} to {arr_airport}"
        
        carriers = [("中華航空", "CI"), ("長榮航空", "BR"), ("星宇航空", "JX"), ("台灣虎航", "IT")]
        
        flight_slots = [
            {"dep_time": "07:30 - 11:45", "ret_time": "12:55 - 17:15", "dep_num": "100", "ret_num": "101", "price_mod": 2000, "site": "Trip.com"},
            {"dep_time": "13:15 - 17:30", "ret_time": "18:40 - 22:55", "dep_num": "104", "ret_num": "105", "price_mod": 0, "site": "航空公司官網"},
            {"dep_time": "18:45 - 23:00", "ret_time": "08:15 - 12:35", "dep_num": "108", "ret_num": "109", "price_mod": -2500, "site": "Skyscanner"}
        ]
        
        for dep_carrier_name, dep_code in carriers:
            for ret_carrier_name, ret_code in carriers:
                for combo in flight_slots:
                    if dep_airport == "TPE" and arr_airport == "NRT":
                        base_dep, base_ret = 12000 if dep_code != "IT" else 6500, 12000 if ret_code != "IT" else 6500
                    elif dep_airport == "TPE" and arr_airport == "BKK":
                        base_dep, base_ret = 10000 if dep_code != "IT" else 5000, 10000 if ret_code != "IT" else 5000
                    else:
                        base_dep, base_ret = 9000, 9000
                    
                    day_offset = random.randint(-3, 3)
                    sim_dep_date = dep_date + timedelta(days=day_offset)
                    sim_ret_date = ret_date + timedelta(days=day_offset)
                    
                    random.seed(len(dep_carrier_name) + len(ret_carrier_name) + combo["price_mod"] + day_offset)
                    
                    single_round_price = (base_dep + (combo["price_mod"] // 2) + random.randint(-400, 600)) + (base_ret + (combo["price_mod"] // 2) + random.randint(-400, 600))
                    if single_round_price < 6000: single_round_price = 6000
                    
                    if add_luggage:
                        if dep_code == "IT": single_round_price += 600  
                        if ret_code == "IT": single_round_price += 600  
                            
                    if add_tax:
                        single_round_price = int(single_round_price * 1.015)
                        
                    full_carrier_display = f"{dep_carrier_name} to {ret_carrier_name}"
                    full_flight_codes = f"{dep_code}{combo['dep_num']} to {ret_code}{combo['ret_num']}"
                    full_slot_display = f"{combo['dep_time']} to {combo['ret_time']}"
                    
                    collected_rows.append([
                        sim_dep_date.strftime('%Y-%m-%d'), sim_ret_date.strftime('%Y-%m-%d'),
                        route_display, full_carrier_display, full_flight_codes,
                        full_slot_display, pax, single_round_price, pax * single_round_price, combo["site"]
                    ])
                    
        new_data_df = pd.DataFrame(collected_rows, columns=columns_list)
        new_data_df = new_data_df.sort_values(by="單人總票價(來回)", ascending=True).reset_index(drop=True)
        new_data_df.to_csv(DB_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.success("成功啟用智慧拆單與行李公平篩選演算法！請切換右側分頁查看。")

# ==================== 📊 右側：儀表板 ＋ 【動態個性化走勢分析】 ====================
with right_col:
    df_display = pd.read_csv(DB_FILE, encoding='utf-8-sig')
    
    if len(df_display) > 0:
        target_route = f"{dep_airport} to {arr_airport}"
        df_final_view = df_display[df_display['去/回程航線'].str.upper() == target_route.upper()]
        df_final_view = df_final_view.sort_values(by="單人總票價(來回)", ascending=True).reset_index(drop=True)
    else:
        df_final_view = df_display

    total_count = len(df_final_view)
    avg_total = int(df_final_view["單人總票價(來回)"].mean()) if total_count > 0 else 0
    max_total = int(df_final_view["單人總票價(來回)"].max()) if total_count > 0 else 0
    min_total = int(df_final_view["單人總票價(來回)"].min()) if total_count > 0 else 0
        
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div style='background: #1E293B; padding: 20px; border-radius: 12px; border: 1px solid #334155;'><span style='color:#94A3B8; font-size:12px;'>TOTAL COMBOS</span><h2 style='margin:10px 0 0 0; font-weight:700;'>{total_count} 組</h2></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div style='background: #1E293B; padding: 20px; border-radius: 12px; border: 1px solid #334155;'><span style='color:#94A3B8; font-size:12px;'>AVERAGE EXPENSE</span><h2 style='margin:10px 0 0 0; color:#3B82F6; font-weight:700;'>${avg_total:,}</h2></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div style='background: #1E293B; padding: 20px; border-radius: 12px; border: 1px solid #334155;'><span style='color:#94A3B8; font-size:12px;'>HIGHEST EXPENSE</span><h2 style='margin:10px 0 0 0; color:#10B981; font-weight:700;'>${max_total:,}</h2></div>", unsafe_allow_html=True)
    
    st.write("") 
    
    # 🌟 調整點：紅框處的分析標題已全面動態變數化，隨使用者輸入即時變更
    if total_count > 0:
        st.info(f"""
            💡 **{user_name} 智慧大數據走勢分析：**
            * 當前航線 `{target_route}` 的歷史來回機票區間：最高 `${max_total:,} TWD`，最低 `${min_total:,} TWD`。
            * ** 智慧旅遊建議：** 目前的比價結果已根據您左側的行李和手續費勾選進行了『跨航司公平權重換算』，最新全網低價屬於健康推薦區間，可安心前往平台開票！
        """)
        st.write("")
    
    tab1, tab2, tab3 = st.tabs(["智慧跨航空低價推薦", "市場數據統計圖表", "原始航班全矩陣總表"])
    
    with tab1:
        if total_count > 0:
            st.write("已為您依據價格由低到高排序：")
            st.write("")
            
            for idx, row in df_final_view.head(5).iterrows():
                carrier_parts = str(row["航空公司"]).split(" to ")
                dep_carrier = carrier_parts[0] if len(carrier_parts) > 0 else str(row["航空公司"])
                ret_carrier = carrier_parts[1] if len(carrier_parts) > 1 else str(row["航空公司"])
                
                code_parts = str(row["航班代號"]).split(" to ")
                dep_code = code_parts[0] if len(code_parts) > 0 else ""
                ret_code = code_parts[1] if len(code_parts) > 1 else ""
                
                time_parts = str(row["航班時間"]).split(" to ")
                dep_time = time_parts[0] if len(time_parts) > 0 else ""
                ret_time = time_parts[1] if len(time_parts) > 1 else ""
                
                with st.container(border=True):
                    if idx == 0:
                        st.markdown("**🏆 自由行首選：全網最省跨航空組合**")
                    else:
                        st.write("常規比價推薦方案")
                        
                    c1, c2, c3 = st.columns([2, 2, 1.5])
                    with c1:
                        st.caption(f"去程日期 · {row['去程日期']}")
                        st.subheader(dep_time)
                        
                        luggage_tag = "🎒 含免費託運行李 (一般航空)" if dep_code != "IT" else "⚠️ 行李需依左側加購 (廉價航空)"
                        st.write(f"**{dep_carrier}** ({dep_code})")
                        st.caption(luggage_tag)
                    with c2:
                        st.caption(f"回程日期 · {row['回程日期']}")
                        st.subheader(ret_time)
                        
                        luggage_tag_ret = "🎒 含免費託運行李 (一般航空)" if ret_code != "IT" else "⚠️ 行李需依左側加購 (廉價航空)"
                        st.write(f"**{ret_carrier}** ({ret_code})")
                        st.caption(luggage_tag_ret)
                    with c3:
                        st.metric(label="來回總票價 (TWD)", value=f"${int(row['單人總票價(來回)']):,}")
                        st.caption(f"平台：{row['可購買網站']}")
                        
                    st.caption(f"航線：{row['去/回程航線']} | 人數：{row['人數']}位")
                st.write("") 
        else:
            st.info("系統安全開機完成！請在左側輸入出發地、目的地並按下搜尋按鈕以解鎖全新的智慧卡片。")
            
    with tab2:
        if total_count > 0:
            st.markdown("### CARRIER TOTAL COST WEIGHT")
            chart_data = df_final_view.groupby("航空公司")["總花費"].sum().reset_index()
            echarts_data = [{"value": int(row["總花費"]), "name": row["航空公司"]} for _, row in chart_data.iterrows()]
            
            options = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "item", "formatter": "{b} : ${c} ({d}%)"},
                "legend": {"top": "5%", "left": "center", "textStyle": {"color": "#94A3B8"}, "type": "scroll"},
                "series": [
                    {
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "avoidLabelOverlap": False,
                        "itemStyle": {"borderRadius": 10, "borderColor": "#0F172A", "borderWidth": 2},
                        "label": {"show": False},
                        "data": echarts_data
                    }
                ]
            }
            st_echarts(options=options, height="350px")
        else:
            st.info("尚無數據可生成圖表。")

    with tab3:
        if total_count > 0:
            t_col1, t_col2 = st.columns([3, 1])
            with t_col1:
                st.markdown("### ALL SCHEDULED FLIGHT DETAILS")
            with t_col2:
                csv_buffer = df_final_view.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="EXPORT CSV", data=csv_buffer, file_name="my_flight_data.csv", mime="text/csv", use_container_width=True)
            
            st.dataframe(df_final_view, use_container_width=True)
        else:
            st.info("尚無矩陣明細。")

# 獨立安全區
st.write("---")
with st.expander("Danger Zone"):
    st.write("點擊下方按鈕將會重置所有歷史機票紀錄。")
    clear_btn = st.button("RESET DATABASE")
    if clear_btn:
        init_csv()
        st.warning("所有數據已清空，請重整網頁。")