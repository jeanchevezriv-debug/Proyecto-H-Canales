# -*- coding: utf-8 -*-
"""
H Canales en Python - Calculadora visual de canales abiertos
Autor: Generado para uso académico

Ejecutar con:
    streamlit run h_canales_app.py
"""

import math
from dataclasses import dataclass
from typing import Dict, Tuple

import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

st.set_page_config(
    page_title="H Canales Python",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #061826 0%, #0b2742 45%, #123f63 100%);
        color: #f8fbff;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071829 0%, #0d2b45 100%);
        border-right: 1px solid rgba(255,255,255,0.12);
    }
    .main-title {
        padding: 26px 28px;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(38,166,255,0.28), rgba(0,215,167,0.18));
        border: 1px solid rgba(255,255,255,0.16);
        box-shadow: 0 18px 50px rgba(0,0,0,0.28);
        margin-bottom: 20px;
    }
    .main-title h1 {
        margin: 0;
        font-size: 2.6rem;
        letter-spacing: 0.5px;
        color: white;
    }
    .main-title p {
        margin-top: 8px;
        color: #d8ecff;
        font-size: 1.05rem;
    }
    .glass-card {
        padding: 20px 22px;
        border-radius: 22px;
        background: rgba(255,255,255,0.095);
        border: 1px solid rgba(255,255,255,0.16);
        box-shadow: 0 14px 38px rgba(0,0,0,0.22);
        backdrop-filter: blur(10px);
        margin-bottom: 18px;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 750;
        color: #ffffff;
        margin-bottom: 10px;
    }
    .mini-note {
        color: #b7d7ef;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .metric-card {
        padding: 16px 16px;
        border-radius: 18px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        margin-bottom: 12px;
    }
    .metric-card small {
        display: block;
        color: #b9d8f0;
        font-size: 0.82rem;
        margin-bottom: 5px;
    }
    .metric-card b {
        color: #ffffff;
        font-size: 1.25rem;
    }
    .ok-pill {
        display: inline-block;
        padding: 8px 13px;
        border-radius: 999px;
        background: rgba(0, 215, 167, 0.18);
        border: 1px solid rgba(0, 215, 167, 0.34);
        color: #baffef;
        font-weight: 700;
    }
    .warn-pill {
        display: inline-block;
        padding: 8px 13px;
        border-radius: 999px;
        background: rgba(255, 193, 7, 0.18);
        border: 1px solid rgba(255, 193, 7, 0.36);
        color: #fff0b7;
        font-weight: 700;
    }
    .danger-pill {
        display: inline-block;
        padding: 8px 13px;
        border-radius: 999px;
        background: rgba(255, 82, 82, 0.18);
        border: 1px solid rgba(255, 82, 82, 0.36);
        color: #ffd2d2;
        font-weight: 700;
    }
    .stButton > button {
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.20);
        background: linear-gradient(135deg, #16a3ff, #00c7a7);
        color: white;
        font-weight: 800;
        padding: 0.65rem 1.1rem;
        box-shadow: 0 12px 28px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetricValue"] {
        color: white;
    }
    div[data-testid="stMetricLabel"] {
        color: #d8ecff;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# MODELO HIDRAULICO
# ============================================================

@dataclass
class Geometry:
    area: float
    wetted_perimeter: float
    hydraulic_radius: float
    top_width: float
    hydraulic_depth: float


def manning_factor(system: str) -> float:
    return 1.486 if system == "Sistema inglés" else 1.0


def gravity(system: str) -> float:
    return 32.174 if system == "Sistema inglés" else 9.81


def unit_labels(system: str) -> Dict[str, str]:
    if system == "Sistema inglés":
        return {
            "length": "ft",
            "area": "ft²",
            "flow": "ft³/s",
            "velocity": "ft/s",
            "slope": "ft/ft",
        }
    return {
        "length": "m",
        "area": "m²",
        "flow": "m³/s",
        "velocity": "m/s",
        "slope": "m/m",
    }


def geometry(section: str, y: float, b: float = 0.0, z: float = 0.0, D: float = 0.0, c_parabola: float = 0.0) -> Geometry:
    if y <= 0:
        raise ValueError("El tirante y debe ser mayor que cero.")

    if section == "Rectangular":
        if b <= 0:
            raise ValueError("Para sección rectangular, la base b debe ser mayor que cero.")
        A = b * y
        P = b + 2 * y
        T = b

    elif section == "Trapezoidal":
        if b < 0:
            raise ValueError("Para sección trapezoidal, la base b no puede ser negativa.")
        if z < 0:
            raise ValueError("Para sección trapezoidal, el talud z no puede ser negativo.")
        A = (b + z * y) * y
        P = b + 2 * y * math.sqrt(1 + z**2)
        T = b + 2 * z * y

    elif section == "Triangular":
        if z <= 0:
            raise ValueError("Para sección triangular, el talud z debe ser mayor que cero.")
        A = z * y**2
        P = 2 * y * math.sqrt(1 + z**2)
        T = 2 * z * y

    elif section == "Circular":
        if D <= 0:
            raise ValueError("Para sección circular, el diámetro D debe ser mayor que cero.")
        if y >= D:
            raise ValueError("En canal circular abierto debe cumplirse y < D.")
        theta = 2 * math.acos(1 - 2 * y / D)  # radianes
        A = (D**2 / 8) * (theta - math.sin(theta))
        P = (D / 2) * theta
        T = D * math.sin(theta / 2)

    elif section == "Parabólica":
        if c_parabola <= 0:
            raise ValueError("Para sección parabólica, el coeficiente C debe ser mayor que cero.")
        # T = C sqrt(y)
        T = c_parabola * math.sqrt(y)
        A = (2 / 3) * T * y
        P = T + (8 * y**2) / (3 * T)  # aproximación usual de la tabla

    else:
        raise ValueError("Tipo de sección no reconocido.")

    if A <= 0 or P <= 0 or T <= 0:
        raise ValueError("La geometría resultó inválida. Revise los datos ingresados.")

    R = A / P
    d = A / T
    return Geometry(A, P, R, T, d)


def manning_Q(section: str, y: float, b: float, z: float, D: float, c_parabola: float, n: float, S: float, system: str) -> Tuple[float, Geometry]:
    if n <= 0:
        raise ValueError("El coeficiente n de Manning debe ser mayor que cero.")
    if S <= 0:
        raise ValueError("La pendiente S debe ser mayor que cero.")

    g = geometry(section, y, b, z, D, c_parabola)
    k = manning_factor(system)
    Q = (k / n) * g.area * (g.hydraulic_radius ** (2 / 3)) * math.sqrt(S)
    return Q, g


def normal_depth(section: str, Q_target: float, b: float, z: float, D: float, c_parabola: float, n: float, S: float, system: str) -> float:
    if Q_target <= 0:
        raise ValueError("El caudal Q debe ser mayor que cero.")

    y_min = 1e-7

    if section == "Circular":
        if D <= 0:
            raise ValueError("Para sección circular, el diámetro D debe ser mayor que cero.")
        y_max = 0.938 * D
        Q_max, _ = manning_Q(section, y_max, b, z, D, c_parabola, n, S, system)
        if Q_target > Q_max:
            raise ValueError("El caudal dado excede la capacidad máxima aproximada del canal circular abierto.")
    else:
        y_max = max(1.0, b if b > 0 else 1.0, D if D > 0 else 1.0)
        for _ in range(120):
            Q_max, _ = manning_Q(section, y_max, b, z, D, c_parabola, n, S, system)
            if Q_max >= Q_target:
                break
            y_max *= 2
        else:
            raise ValueError("No se logró encontrar un rango razonable para el tirante normal.")

    for _ in range(120):
        y_mid = (y_min + y_max) / 2
        Q_mid, _ = manning_Q(section, y_mid, b, z, D, c_parabola, n, S, system)
        if Q_mid < Q_target:
            y_min = y_mid
        else:
            y_max = y_mid

    return (y_min + y_max) / 2


def flow_regime(fr: float) -> str:
    if fr < 0.95:
        return "Subcrítico"
    if fr > 1.05:
        return "Supercrítico"
    return "Crítico aproximado"


# ============================================================
# DIBUJO DE SECCIONES
# ============================================================

def add_trace_polygon(fig, x, y, name, fill_color, line_color="#dcecff"):
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            fill="toself",
            name=name,
            line=dict(color=line_color, width=3),
            fillcolor=fill_color,
            hoverinfo="skip",
        )
    )


def section_figure(section: str, y: float, b: float, z: float, D: float, c_parabola: float) -> go.Figure:
    fig = go.Figure()
    water = "rgba(40, 180, 255, 0.55)"
    wall = "rgba(255, 255, 255, 0.0)"
    edge = "#eaf7ff"

    try:
        if section == "Rectangular" and b > 0 and y > 0:
            x = [-b/2, -b/2, b/2, b/2, -b/2]
            yy = [y, 0, 0, y, y]
            add_trace_polygon(fig, x, yy, "Agua", water, edge)
            fig.add_annotation(x=0, y=y*1.08, text="T = b", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=b/2*1.08, y=y/2, text="y", showarrow=False, font=dict(color="white", size=14))

        elif section == "Trapezoidal" and y > 0 and z >= 0:
            T = b + 2*z*y
            x = [-T/2, -b/2, b/2, T/2, -T/2]
            yy = [y, 0, 0, y, y]
            add_trace_polygon(fig, x, yy, "Agua", water, edge)
            fig.add_annotation(x=0, y=y*1.08, text="T = b + 2zy", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=0, y=-0.08*y, text="b", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=T/2*0.82, y=y/2, text="z:1", showarrow=False, font=dict(color="white", size=14))

        elif section == "Triangular" and y > 0 and z > 0:
            T = 2*z*y
            x = [-T/2, 0, T/2, -T/2]
            yy = [y, 0, y, y]
            add_trace_polygon(fig, x, yy, "Agua", water, edge)
            fig.add_annotation(x=0, y=y*1.08, text="T = 2zy", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=T/2*0.55, y=y/2, text="z:1", showarrow=False, font=dict(color="white", size=14))

        elif section == "Circular" and D > 0 and 0 < y < D:
            r = D/2
            alpha = math.acos(1 - 2*y/D)
            ts = [-alpha + 2*alpha*i/120 for i in range(121)]
            x_arc = [r*math.sin(t) for t in ts]
            y_arc = [r - r*math.cos(t) for t in ts]
            x_poly = x_arc + [x_arc[-1], x_arc[0]]
            y_poly = y_arc + [y, y]
            add_trace_polygon(fig, x_poly, y_poly, "Agua", water, edge)

            # contorno completo del tubo
            ts2 = [2*math.pi*i/240 for i in range(241)]
            fig.add_trace(go.Scatter(
                x=[r*math.cos(t) for t in ts2],
                y=[r + r*math.sin(t) for t in ts2],
                mode="lines",
                line=dict(color="#eaf7ff", width=3),
                name="Contorno",
                hoverinfo="skip",
            ))
            fig.add_annotation(x=0, y=D*1.04, text="D", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=r*0.9, y=y/2, text="y", showarrow=False, font=dict(color="white", size=14))

        elif section == "Parabólica" and c_parabola > 0 and y > 0:
            hs = [y*i/120 for i in range(121)]
            left_x = [-(c_parabola*math.sqrt(h))/2 for h in hs]
            right_x = [(c_parabola*math.sqrt(h))/2 for h in reversed(hs)]
            x = left_x + right_x
            yy = hs + list(reversed(hs))
            add_trace_polygon(fig, x, yy, "Agua", water, edge)
            T = c_parabola * math.sqrt(y)
            fig.add_annotation(x=0, y=y*1.08, text="T = C√y", showarrow=False, font=dict(color="white", size=14))
            fig.add_annotation(x=T*0.42, y=y/2, text="y", showarrow=False, font=dict(color="white", size=14))

        else:
            fig.add_annotation(x=0, y=0, text="Ingrese datos válidos para visualizar la sección", showarrow=False, font=dict(color="white", size=16))

    except Exception:
        fig.add_annotation(x=0, y=0, text="Vista no disponible con los datos actuales", showarrow=False, font=dict(color="white", size=16))

    fig.update_layout(
        height=410,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.06)",
        showlegend=False,
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
    )
    return fig


def card(label: str, value: str):
    st.markdown(f"""
        <div class="metric-card">
            <small>{label}</small>
            <b>{value}</b>
        </div>
    """, unsafe_allow_html=True)


def fmt(value: float, digits: int = 6) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    if abs(value) >= 10000 or (abs(value) < 0.001 and value != 0):
        return f"{value:.4e}"
    return f"{value:.{digits}g}"


# ============================================================
# INTERFAZ
# ============================================================

st.markdown(
    """
    <div class="main-title">
        <h1>💧 H Canales en Python</h1>
        <p>Calculadora visual de canales abiertos usando geometría hidráulica y fórmula de Manning.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    section = st.selectbox(
        "Tipo de sección",
        ["Rectangular", "Trapezoidal", "Triangular", "Circular", "Parabólica"],
        index=1,
    )
    system = st.selectbox("Sistema de unidades", ["Sistema internacional", "Sistema inglés"], index=0)
    solve_mode = st.radio(
        "Modo de cálculo",
        ["Calcular caudal Q", "Calcular tirante normal y"],
        index=0,
    )

    labels = unit_labels(system)

    st.markdown("---")
    st.markdown("### 📥 Datos hidráulicos")
    n = st.number_input("n de Manning", min_value=0.0001, value=0.015, step=0.001, format="%.4f")
    S = st.number_input(f"Pendiente S ({labels['slope']})", min_value=0.000001, value=0.001, step=0.0001, format="%.6f")

    Q_input = 1.0
    y_input = 1.0

    if solve_mode == "Calcular caudal Q":
        y_input = st.number_input(f"Tirante y ({labels['length']})", min_value=0.0001, value=1.0, step=0.10, format="%.4f")
    else:
        Q_input = st.number_input(f"Caudal Q ({labels['flow']})", min_value=0.0001, value=1.0, step=0.10, format="%.4f")

    st.markdown("---")
    st.markdown("### 📐 Datos geométricos")

    b = 0.0
    z = 0.0
    D = 0.0
    c_parabola = 0.0

    if section in ["Rectangular", "Trapezoidal"]:
        b = st.number_input(f"Base b ({labels['length']})", min_value=0.0 if section == "Trapezoidal" else 0.0001, value=2.0, step=0.10, format="%.4f")
    if section in ["Trapezoidal", "Triangular"]:
        z = st.number_input("Talud z, horizontal por 1 vertical", min_value=0.0 if section == "Trapezoidal" else 0.0001, value=1.0, step=0.10, format="%.4f")
    if section == "Circular":
        D = st.number_input(f"Diámetro D ({labels['length']})", min_value=0.0001, value=1.5, step=0.10, format="%.4f")
    if section == "Parabólica":
        c_parabola = st.number_input("Coeficiente C para T = C√y", min_value=0.0001, value=2.0, step=0.10, format="%.4f")

    st.markdown("---")
    calculate = st.button("Calcular", use_container_width=True)

left, right = st.columns([1.08, 1.0], gap="large")

if not calculate:
    # Calcula automáticamente con los valores actuales para que la app siempre se vea viva.
    calculate = True

try:
    if solve_mode == "Calcular tirante normal y":
        y_calc = normal_depth(section, Q_input, b, z, D, c_parabola, n, S, system)
        Q_calc, geo = manning_Q(section, y_calc, b, z, D, c_parabola, n, S, system)
        y_used = y_calc
    else:
        y_used = y_input
        Q_calc, geo = manning_Q(section, y_used, b, z, D, c_parabola, n, S, system)
        y_calc = y_used

    V = Q_calc / geo.area
    Fr = V / math.sqrt(gravity(system) * geo.hydraulic_depth)
    regime = flow_regime(Fr)

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Resultados principales</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            card(f"Caudal Q ({labels['flow']})", fmt(Q_calc))
            card(f"Área A ({labels['area']})", fmt(geo.area))
            card(f"Velocidad V ({labels['velocity']})", fmt(V))
        with c2:
            card(f"Tirante y ({labels['length']})", fmt(y_used))
            card(f"Perímetro P ({labels['length']})", fmt(geo.wetted_perimeter))
            card("Número de Froude", fmt(Fr, 5))
        with c3:
            card(f"Radio R ({labels['length']})", fmt(geo.hydraulic_radius))
            card(f"Ancho T ({labels['length']})", fmt(geo.top_width))
            card(f"Tirante hidráulico d ({labels['length']})", fmt(geo.hydraulic_depth))

        if regime == "Subcrítico":
            st.markdown(f'<span class="ok-pill">Régimen: {regime}</span>', unsafe_allow_html=True)
        elif regime == "Supercrítico":
            st.markdown(f'<span class="danger-pill">Régimen: {regime}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="warn-pill">Régimen: {regime}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🧮 Fórmula usada</div>', unsafe_allow_html=True)
        st.latex(r"Q = \frac{k}{n} A R^{2/3} S^{1/2}")
        st.markdown(
            f"""
            <div class="mini-note">
            Factor utilizado: <b>k = {manning_factor(system)}</b>. &nbsp;
            Sistema seleccionado: <b>{system}</b>.<br>
            La geometría se actualiza según la sección escogida y luego se aplica Manning.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">🖼️ Sección {section}</div>', unsafe_allow_html=True)
        st.plotly_chart(section_figure(section, y_used, b, z, D, c_parabola), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✅ Estado del cálculo</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="mini-note">
            El cálculo se realizó correctamente. Esta versión incluye: sección rectangular, trapezoidal,
            triangular, circular y parabólica; caudal por Manning; tirante normal; velocidad; Froude y régimen de flujo.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    c1, c2 = st.columns([1.1, 1.0], gap="large")
    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚠️ Revisión necesaria</div>', unsafe_allow_html=True)
        st.error(str(e))
        st.markdown(
            """
            Revise que los datos sean positivos y que correspondan a la sección seleccionada.
            Para sección circular abierta debe cumplirse que el tirante sea menor que el diámetro.
            """
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">🖼️ Sección {section}</div>', unsafe_allow_html=True)
        st.plotly_chart(section_figure(section, max(y_input, 0.1), b, z, D, c_parabola), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

