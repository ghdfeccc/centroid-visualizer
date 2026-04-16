import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Центр Масс | Mobile & Desktop", layout="wide")

# 2. Мощный CSS для поддержки мобильных устройств
st.markdown("""
    <style>
    .stApp { 
        background-color: #f0f2f6; 
        background-image: linear-gradient(#d1d4f9 1px, transparent 1px), linear-gradient(90deg, #d1d4f9 1px, transparent 1px); 
        background-size: 30px 30px; 
    }
    /* КРИТИЧНО ДЛЯ ТЕЛЕФОНОВ: Отключаем системные жесты на холсте */
    canvas { 
        touch-action: none !important; 
        -webkit-tap-highlight-color: transparent; 
        user-select: none; 
    }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric), .stTabs, .stDataEditor, [data-testid="stForm"] { 
        background-color: rgba(255, 255, 255, 0.98); 
        padding: 25px; border-radius: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); border: 1px solid #c1c4f7; 
    }
    h1 { color: #003399; background: white; padding: 15px; border-radius: 12px; border-left: 8px solid #ff0000; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Центр масс: Аналитическая система")

# Инициализация памяти приложения
if 'all_points' not in st.session_state:
    st.session_state.all_points = pd.DataFrame(columns=['x', 'y', 'weight'])
if 'canvas_key' not in st.session_state:
    st.session_state.canvas_key = 0

def clear_all():
    st.session_state.all_points = pd.DataFrame(columns=['x', 'y', 'weight'])
    st.session_state.canvas_key += 1

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("📍 Добавление объектов")
    tab1, tab2 = st.tabs(["🖌 Рисовать / Тапать", "🔢 Ввести координаты"])
    
    with tab1:
        st.caption("На телефоне: просто коротко нажимайте на поле")
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=2,
            background_color="#ffffff",
            height=400, width=400,
            drawing_mode="point",
            update_streamlit=True,    # Включаем мгновенную реакцию
            point_display_radius=8,   # Увеличиваем точку для удобства пальца
            key=f"canvas_k_{st.session_state.canvas_key}", 
        )
        
        # Обработка данных с холста (с защитой от бесконечного цикла)
        if canvas_result.json_data is not None:
            df_canvas = pd.json_normalize(canvas_result.json_data["objects"])
            if not df_canvas.empty:
                # Округляем до целых, чтобы микро-сдвиги пальца не создавали новые точки
                new_pts = df_canvas[['left', 'top']].round(0)
                new_pts.columns = ['x', 'y']
                new_pts['weight'] = 1.0
                
                # Добавляем только те, которых реально нет в списке
                old_pts = st.session_state.all_points
                combined = pd.concat([old_pts, new_pts]).drop_duplicates(subset=['x', 'y']).reset_index(drop=True)
                
                if len(combined) != len(old_pts):
                    st.session_state.all_points = combined
                    st.rerun()

    with tab2:
        with st.form("coord_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nx = c1.number_input("X", 0, 400, 200)
            ny = c2.number_input("Y", 0, 400, 200)
            nw = c3.number_input("Масса", 0.1, 1000.0, 1.0)
            if st.form_submit_button("Добавить"):
                new_row = pd.DataFrame({'x': [float(nx)], 'y': [float(ny)], 'weight': [float(nw)]})
                st.session_state.all_points = pd.concat([st.session_state.all_points, new_row]).drop_duplicates(subset=['x', 'y']).reset_index(drop=True)
                st.rerun()

    st.markdown("**📋 Список всех точек:**")
    edited_df = st.data_editor(st.session_state.all_points, num_rows="dynamic", use_container_width=True, key=f"editor_{st.session_state.canvas_key}")
    
    # Синхронизация при удалении из таблицы
    if len(edited_df) < len(st.session_state.all_points):
        st.session_state.all_points = edited_df
        st.session_state.canvas_key += 1
        st.rerun()
    else:
        st.session_state.all_points = edited_df

    st.button("🗑 Очистить всё", on_click=clear_all)

with col2:
    st.subheader("📈 Графический анализ")
    df = st.session_state.all_points
    cx, cy, total_w = 0.0, 0.0, 0.0

    if not df.empty:
        df['x'] = pd.to_numeric(df['x'])
        df['y'] = pd.to_numeric(df['y'])
        df['weight'] = pd.to_numeric(df['weight']).fillna(1.0)
        total_w = df['weight'].sum()
        if total_w != 0:
            cx, cy = (df['x'] * df['weight']).sum() / total_w, (df['y'] * df['weight']).sum() / total_w

        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(x=[row['x'], cx], y=[row['y'], cy], mode='lines', line=dict(color='#cccccc', width=1), showlegend=False))
        
        fig.add_trace(go.Scatter(x=df['x'], y=df['y'], mode='markers', 
                                 marker=dict(color='#0055ff', size=df['weight'].astype(float)*2 + 10, opacity=1.0, line=dict(width=2, color='white')), 
                                 name="Точки"))
        
        fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers', 
                                 marker=dict(color='#ff0000', size=18, symbol='circle', line=dict(width=3, color='white')), 
                                 name="Центр масс"))
        
        fig.update_xaxes(range=[0, 400], side="top", gridcolor='#eeeeee', zeroline=False)
        fig.update_yaxes(range=[400, 0], gridcolor='#eeeeee', zeroline=False)
        fig.update_layout(width=500, height=500, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Центр X", f"{cx:.1f}")
        m2.metric("Центр Y", f"{cy:.1f}")
        m3.metric("Общая масса", f"{total_w:.1f}")
    else:
        st.info("Добавьте точки для расчета.")

st.divider()
st.latex(r"X_c = \frac{\sum x_i w_i}{\sum w_i}, \quad Y_c = \frac{\sum y_i w_i}{\sum w_i}")
