import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Центр Масс | Аналитическая система", layout="wide")

# 2. Стильный CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
        background-image: linear-gradient(#d1d4f9 1px, transparent 1px), linear-gradient(90deg, #d1d4f9 1px, transparent 1px);
        background-size: 30px 30px;
    }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric), .stTabs, .stDataEditor, [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.98);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        border: 1px solid #c1c4f7;
    }
    h1 { color: #003399; background: white; padding: 15px; border-radius: 12px; border-left: 8px solid #ff0000; }
    canvas { touch-action: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Центр масс: Аналитическая система")

# Инициализация сессии
if 'all_points' not in st.session_state:
    st.session_state.all_points = pd.DataFrame(columns=['x', 'y', 'weight'])
if 'editor_key' not in st.session_state:
    st.session_state.editor_key = 0

# Функция для ПОЛНОЙ очистки
def clear_all():
    st.session_state.all_points = pd.DataFrame(columns=['x', 'y', 'weight'])
    st.session_state.editor_key += 1 # Меняем ключ, чтобы редактор "забыл" старые данные
    # Очистка кэша холста происходит через смену ключа или обновление страницы

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("📍 Добавление объектов")
    tab1, tab2 = st.tabs(["🖌 Рисовать на холсте", "🔢 Точные координаты"])
    
    with tab1:
        st.caption("Кликните по полю (Масса по умолчанию: 1.0)")
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=2,
            background_color="#ffffff",
            height=400, width=400,
            drawing_mode="point",
            update_streamlit=True,
            point_display_radius=6,
            key=f"canvas_{st.session_state.editor_key}", # Динамический ключ
        )
        if canvas_result.json_data is not None:
            df_canvas = pd.json_normalize(canvas_result.json_data["objects"])
            if not df_canvas.empty:
                for _, row in df_canvas.iterrows():
                    if not ((st.session_state.all_points['x'] == row['left']) & 
                            (st.session_state.all_points['y'] == row['top'])).any():
                        new_pt = pd.DataFrame({'x': [row['left']], 'y': [row['top']], 'weight': [1.0]})
                        st.session_state.all_points = pd.concat([st.session_state.all_points, new_pt], ignore_index=True)
    
    with tab2:
        with st.form("coord_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nx = c1.number_input("X (0-400)", 0, 400, 200)
            ny = c2.number_input("Y (0-400)", 0, 400, 200)
            nw = c3.number_input("Масса (W)", 0.1, 1000.0, 1.0)
            if st.form_submit_button("Добавить точку"):
                new_row = pd.DataFrame({'x': [nx], 'y': [ny], 'weight': [nw]})
                st.session_state.all_points = pd.concat([st.session_state.all_points, new_row], ignore_index=True)

    st.markdown("**📋 Список точек:**")
    # Используем динамический ключ для мгновенного обнуления редактора
    st.session_state.all_points = st.data_editor(
        st.session_state.all_points, 
        num_rows="dynamic", 
        use_container_width=True,
        key=f"editor_{st.session_state.editor_key}"
    )
    
    # Кнопка очистки вызывает функцию
    st.button("🗑 Очистить всё", on_click=clear_all)

with col2:
    st.subheader("📈 Визуальный анализ")
    df = st.session_state.all_points
    
    cx, cy, total_w = 0.0, 0.0, 0.0

    if not df.empty:
        df['x'] = pd.to_numeric(df['x'])
        df['y'] = pd.to_numeric(df['y'])
        df['weight'] = pd.to_numeric(df['weight']).fillna(1.0)

        total_w = df['weight'].sum()
        if total_w != 0:
            cx = (df['x'] * df['weight']).sum() / total_w
            cy = (df['y'] * df['weight']).sum() / total_w

        fig = go.Figure()
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(x=[row['x'], cx], y=[row['y'], cy], 
                                     mode='lines', line=dict(color='#cccccc', width=1), 
                                     hoverinfo='skip', showlegend=False))
        fig.add_trace(go.Scatter(x=df['x'], y=df['y'], mode='markers',
            marker=dict(color='#0055ff', size=df['weight'].astype(float)*2 + 10, 
                        opacity=1.0, line=dict(width=2, color='white')), name="Точки"))
        fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers',
            marker=dict(color='#ff0000', size=18, symbol='circle', 
                        line=dict(width=3, color='white')), name="Центр масс"))

        fig.update_xaxes(range=[0, 400], side="top", gridcolor='#eeeeee', zeroline=False)
        fig.update_yaxes(range=[400, 0], gridcolor='#eeeeee', zeroline=False)
        fig.update_layout(width=500, height=500, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Добавьте точки на холсте или введите координаты вручную.")

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Центр X", f"{cx:.1f}")
    m2.metric("Центр Y", f"{cy:.1f}")
    m3.metric("Общая масса", f"{total_w:.1f}")

st.divider()
st.latex(r"X_c = \frac{\sum x_i w_i}{\sum w_i}, \quad Y_c = \frac{\sum y_i w_i}{\sum w_i}")
