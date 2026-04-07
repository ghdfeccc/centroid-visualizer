import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Центроид Проект", layout="wide")

# Исправление смещения: принудительно задаем стиль для контейнера холста
st.markdown("""
    <style>
    iframe { border: 1px solid #ddd; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Аналитическая система поиска центроида")

# Создаем состояние сессии для хранения точек, введенных вручную
if 'manual_points' not in st.session_state:
    st.session_state.manual_points = []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Добавление точек")

    tab1, tab2 = st.tabs(["✍️ Рисовать мышкой", "🔢 Ввести координаты"])

    with tab1:
        st.caption("Кликайте на поле (размер 400x400)")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#1f77b4",
            background_color="#ffffff",
            height=400,
            width=400,
            drawing_mode="point",
            key="canvas",
        )

    with tab2:
        with st.form("coord_form"):
            new_x = st.number_input("Координата X (0-400)", 0, 400, 200)
            new_y = st.number_input("Координата Y (0-400)", 0, 400, 200)
            add_btn = st.form_submit_button("Добавить точку")
            if add_btn:
                st.session_state.manual_points.append({'left': new_x, 'top': new_y})

        if st.button("Очистить ручной ввод"):
            st.session_state.manual_points = []
            st.rerun()

with col2:
    st.subheader("2. Визуализация и расчет")

    # Собираем все точки: с холста + ручные
    all_points = []
    if canvas_result.json_data is not None:
        canvas_points = pd.json_normalize(canvas_result.json_data["objects"])
        if not canvas_points.empty:
            all_points.extend(canvas_points[['left', 'top']].to_dict('records'))

    all_points.extend(st.session_state.manual_points)

    if all_points:
        df = pd.DataFrame(all_points)
        cx, cy = df['left'].mean(), df['top'].mean()

        fig = go.Figure()

        # Линии к центроиду
        for _, row in df.iterrows():
            fig.add_trace(go.Scatter(x=[row['left'], cx], y=[row['top'], cy],
                                     mode='lines', line=dict(color='gray', width=1),
                                     showlegend=False, opacity=0.3))

        # Обычные точки
        fig.add_trace(go.Scatter(x=df['left'], y=df['top'], mode='markers',
                                 marker=dict(color='royalblue', size=10), name="Точки"))

        # Центроид
        fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers',
                                 marker=dict(color='red', size=15, symbol='cross'), name="Центроид"))

        # Настройка осей (инверсия Y для соответствия холсту)
        fig.update_xaxes(range=[0, 400], side="top")
        fig.update_yaxes(range=[400, 0])
        fig.update_layout(width=450, height=450, template="simple_white")

        st.plotly_chart(fig)

        st.success(f"**Центроид найден:** X={cx:.2f}, Y={cy:.2f}")
        st.dataframe(df, height=150)  # Показать таблицу координат
    else:
        st.info("Добавьте точки, чтобы увидеть результат.")

st.divider()
st.latex(r"x_c = \frac{1}{n}\sum_{i=1}^n x_i, \quad y_c = \frac{1}{n}\sum_{i=1}^n y_i")
