import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Настройка страницы и темы
st.set_page_config(page_title="Центр Масс Системы", layout="wide")

# Кастомный CSS для крутого инженерного фона (сетка)
st.markdown("""
    <style>
    .stApp {
        background-color: #e5e5f7;
        background-image: linear-gradient(#c1c4f7 1px, transparent 1px), linear-gradient(90deg, #c1c4f7 1px, transparent 1px);
        background-size: 30px 30px;
    }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric), .stTabs, .stDataEditor, [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    h1 { color: #1f3a93; background: rgba(255,255,255,0.8); padding: 10px; border-radius: 10px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Визуализатор центра масс системы")

# Инициализация хранилища точек в сессии
if 'all_points' not in st.session_state:
    st.session_state.all_points = pd.DataFrame(columns=['x', 'y', 'weight'])

# 2. Основной интерфейс
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("🛠 Ввод данных")
    tab1, tab2 = st.tabs(["🖌 Рисовать", "🔢 Ввести координаты"])
    
    with tab1:
        st.caption("Кликайте по холсту, чтобы добавить точки")
        canvas_result = st_canvas(
            fill_color="rgba(255, 75, 75, 0.3)",
            stroke_width=2,
            background_color="#ffffff",
            height=400, width=400,
            drawing_mode="point",
            key="canvas",
        )
        # Если кликнули на холст — добавляем точку
        if canvas_result.json_data is not None:
            df_canvas = pd.json_normalize(canvas_result.json_data["objects"])
            if not df_canvas.empty:
                for _, row in df_canvas.iterrows():
                    # Проверка на дубликаты координат
                    if not ((st.session_state.all_points['x'] == row['left']) & 
                            (st.session_state.all_points['y'] == row['top'])).any():
                        new_pt = pd.DataFrame({'x': [row['left']], 'y': [row['top']], 'weight': [5.0]})
                        st.session_state.all_points = pd.concat([st.session_state.all_points, new_pt], ignore_index=True)
    
    with tab2:
        with st.form("coord_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nx = c1.number_input("X (0-400)", 0, 400, 200)
            ny = c2.number_input("Y (0-400)", 0, 400, 200)
            nw = c3.number_input("Масса", 0.1, 1000.0, 10.0)
            if st.form_submit_button("Добавить точку"):
                new_row = pd.DataFrame({'x': [nx], 'y': [ny], 'weight': [nw]})
                st.session_state.all_points = pd.concat([st.session_state.all_points, new_row], ignore_index=True)

    st.write("**Редактор масс и удаление:**")
    st.caption("Чтобы удалить точку: выделите строку и нажмите Delete")
    # Динамический редактор (позволяет менять вес и удалять строки)
    st.session_state.all_points = st.data_editor(
        st.session_state.all_points, 
        num_rows="dynamic", 
        use_container_width=True,
        key="main_editor"
    )

with col2:
    st.subheader("📊 Графический анализ")
    df = st.session_state.all_points
    
    if not df.empty:
        # Принудительная типизация данных (лечит ошибки Plotly)
        df['x'] = pd.to_numeric(df['x'])
        df['y'] = pd.to_numeric(df['y'])
        df['weight'] = pd.to_numeric(df['weight']).fillna(1.0)

        total_w = df['weight'].sum()
        if total_w != 0:
            cx = (df['x'] * df['weight']).sum() / total_w
            cy = (df['y'] * df['weight']).sum() / total_w
        else:
            cx, cy = 0, 0

        fig = go.Figure()

        # 1. Линии связи (паутина)
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(x=[row['x'], cx], y=[row['top'] if 'top' in row else row['y'], cy], 
                                     mode='lines', line=dict(color='#d0d0d0', width=0.5), 
                                     hoverinfo='skip', showlegend=False))

        # 2. Сами точки (размер зависит от массы)
        fig.add_trace(go.Scatter(
            x=df['x'], y=df['y'], mode='markers',
            marker=dict(color='#4b8bbe', size=df['weight'].astype(float)*0.5 + 8, 
                        opacity=0.8, line=dict(width=1, color='white')),
            name="Точки массы"
        ))

        # 3. Центр масс (прицел)
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy], mode='markers',
            marker=dict(color='rgba(255, 75, 75, 0.4)', size=15, symbol='circle-open-dot', 
                        line=dict(width=2, color='red')),
            name="Центр масс"
        ))

        # Настройка осей (инверсия Y под холст)
        fig.update_xaxes(range=[0, 400], side="top", showgrid=True, gridcolor='lightgray')
        fig.update_yaxes(range=[400, 0], showgrid=True, gridcolor='lightgray')
        fig.update_layout(width=500, height=500, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white")

        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Координата X_c", f"{cx:.1f}")
        m2.metric("Координата Y_c", f"{cy:.1f}")
        m3.metric("Общая масса", f"{total_w:.1f}")
    else:
        st.info("Добавьте точки на холсте или через форму ввода")

st.markdown("---")
st.latex(r"X_c = \frac{\sum x_i w_i}{\sum w_i}, \quad Y_c = \frac{\sum y_i w_i}{\sum w_i}")
