# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import json
from datetime import datetime

DB_PATH = "finance.db"

st.set_page_config(page_title="Controle Financeiro — Dark (Com Histórico)", layout="wide", initial_sidebar_state="expanded")

# --- Database helpers ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    start_balance REAL,
                    monthly_income REAL,
                    created_at TEXT
                );""")
    c.execute("""CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    item TEXT,
                    value REAL,
                    created_at TEXT
                );""")
    c.execute("""CREATE TABLE IF NOT EXISTS projections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    months INTEGER,
                    final_balance REAL,
                    series_json TEXT,
                    created_at TEXT
                );""")
    conn.commit()
    conn.close()

def save_user(conn, name, start_balance, monthly_income):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute("INSERT INTO users (name, start_balance, monthly_income, created_at) VALUES (?,?,?,?)",
              (name, start_balance, monthly_income, created_at))
    conn.commit()
    return c.lastrowid

def save_expenses(conn, user_id, df, category):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    for _, row in df.iterrows():
        item = str(row.get("item","")).strip()
        try:
            value = float(row.get("valor", 0.0))
        except:
            value = 0.0
        if item != "":
            c.execute("INSERT INTO expenses (user_id, category, item, value, created_at) VALUES (?,?,?,?,?)",
                      (user_id, category, item, value, created_at))
    conn.commit()

def save_projection(conn, user_id, months, final_balance, series_df):
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    series_json = series_df.to_json(orient="records", force_ascii=False)
    c.execute("INSERT INTO projections (user_id, months, final_balance, series_json, created_at) VALUES (?,?,?,?,?)",
              (user_id, months, final_balance, series_json, created_at))
    conn.commit()

def load_projections(conn, user_id=None):
    c = conn.cursor()
    if user_id:
        c.execute("SELECT id, months, final_balance, series_json, created_at FROM projections WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    else:
        c.execute("SELECT id, months, final_balance, series_json, created_at FROM projections ORDER BY created_at DESC")
    rows = c.fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "months": r[1],
            "final_balance": r[2],
            "series": json.loads(r[3]),
            "created_at": r[4]
        })
    return out

# --- Financial helpers ---
def sum_df(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return 0.0
    return float(pd.to_numeric(df.get("valor", pd.Series([])), errors="coerce").fillna(0.0).sum())

def projection_series(start_balance: float, monthly_income: float, fixed_total: float, variable_total: float, months: int) -> pd.DataFrame:
    rows = []
    balance = start_balance
    monthly_net = monthly_income - (fixed_total + variable_total)
    for m in range(1, months + 1):
        balance = balance + monthly_net
        rows.append({"month": (pd.Timestamp.now().replace(day=1) + pd.DateOffset(months=m)).strftime("%Y-%m"), "balance": round(balance, 2)})
    return pd.DataFrame(rows)

def status_indicator(balance: float):
    if balance >= 0:
        return "Positivo", "✅"
    return "Negativo", "⚠️"

# --- Init DB ---
init_db()

# --- Sidebar inputs ---
st.sidebar.header("Configurações do Usuário")
name = st.sidebar.text_input("Nome do usuário", value="Usuário")
start_balance = st.sidebar.number_input("Saldo atual (R$)", min_value=-1_000_000.0, value=500.0, step=50.0, format="%.2f")
monthly_income = st.sidebar.number_input("Renda mensal (R$)", min_value=0.0, value=2500.0, step=100.0, format="%.2f")

st.sidebar.markdown("---")
st.sidebar.subheader("Despesas fixas (edite)")
if "fixed" not in st.session_state:
    st.session_state.fixed = pd.DataFrame([
        {"item": "Aluguel", "valor": 1200.00},
        {"item": "Energia", "valor": 150.00},
        {"item": "Internet", "valor": 100.00},
        {"item": "Transporte", "valor": 200.00}
    ])

fixed_df = st.sidebar.data_editor(st.session_state.fixed, num_rows="dynamic", use_container_width=True)
st.session_state.fixed = fixed_df

st.sidebar.markdown("---")
st.sidebar.subheader("Despesas variáveis (edite)")
if "variable" not in st.session_state:
    st.session_state.variable = pd.DataFrame([
        {"item": "Supermercado", "valor": 450.00},
        {"item": "Lazer", "valor": 200.00},
        {"item": "Compras", "valor": 120.00}
    ])

var_df = st.sidebar.data_editor(st.session_state.variable, num_rows="dynamic", use_container_width=True)
st.session_state.variable = var_df

st.sidebar.markdown("---")
months = st.sidebar.slider("Projeção (meses)", min_value=1, max_value=24, value=6)
simulate_future_cost = st.sidebar.number_input("Despesas futuras pontuais (R$)", min_value=0.0, value=0.0, format="%.2f")

if st.sidebar.button("Salvar dados no banco" ):
    conn = sqlite3.connect(DB_PATH)
    try:
        user_id = save_user(conn, name, start_balance, monthly_income)
        save_expenses(conn, user_id, st.session_state.fixed, "fixa")
        save_expenses(conn, user_id, st.session_state.variable, "variavel")
        st.sidebar.success("Dados salvos com sucesso.")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar: {e}")
    finally:
        conn.close()

if st.sidebar.button("Salvar projeção atual" ):
    conn = sqlite3.connect(DB_PATH)
    try:
        fixed_total = sum_df(st.session_state.fixed)
        variable_total = sum_df(st.session_state.variable)
        proj_df = projection_series(start_balance - simulate_future_cost, monthly_income, fixed_total, variable_total, months)
        final_balance = proj_df['balance'].iloc[-1] if not proj_df.empty else start_balance
        # create a user row first (or anonymous)
        user_id = save_user(conn, name, start_balance, monthly_income)
        save_projection(conn, user_id, months, float(final_balance), proj_df)
        st.sidebar.success("Projeção salva com sucesso.")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar projeção: {e}")
    finally:
        conn.close()

st.sidebar.markdown("---")
st.sidebar.subheader("Histórico de projeções salvas")
conn = sqlite3.connect(DB_PATH)
history = load_projections(conn)
conn.close()
if history:
    hist_df = pd.DataFrame([{
        'id': h['id'],
        'months': h['months'],
        'final_balance': h['final_balance'],
        'created_at': h['created_at']
    } for h in history])
    st.sidebar.dataframe(hist_df.sort_values('created_at', ascending=False).reset_index(drop=True), use_container_width=True, height=220)
else:
    st.sidebar.info("Nenhuma projeção salva.")

# --- Main layout ---
st.markdown(f"## Olá, **{name}**")
st.markdown("#### Resumo financeiro")

fixed_total = sum_df(st.session_state.fixed)
variable_total = sum_df(st.session_state.variable)
total_despesas = fixed_total + variable_total + simulate_future_cost
monthly_net = monthly_income - (fixed_total + variable_total)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Renda mensal (R$)", f"{monthly_income:,.2f}")
col2.metric("Despesas mensais (R$)", f"{(fixed_total + variable_total):,.2f}")
col3.metric("Saldo atual (R$)", f"{start_balance:,.2f}")
status_text, status_emoji = status_indicator(start_balance + monthly_net)
col4.metric("Situação (mensal)", f"{status_text} {status_emoji}", delta=f"{monthly_net:,.2f}")

st.markdown("---")

left, right = st.columns([1.4, 1])

with left:
    st.subheader("Detalhamento das despesas")
    tab1, tab2 = st.tabs(["Fixas", "Variáveis"])
    with tab1:
        st.dataframe(st.session_state.fixed.style.format({"valor":"R$ {:,.2f}"}), height=220)
        st.write(f"Total fixas: R$ {fixed_total:,.2f}")
    with tab2:
        st.dataframe(st.session_state.variable.style.format({"valor":"R$ {:,.2f}"}), height=220)
        st.write(f"Total variáveis: R$ {variable_total:,.2f}")

    st.subheader("Despesas futuras pontuais")
    st.write(f"Valor informado: R$ {simulate_future_cost:,.2f}")

with right:
    st.subheader("Distribuição de despesas (atualiza em tempo real)")
    breakdown = pd.DataFrame({
        "categoria": ["Fixas", "Variáveis", "Futuras"],
        "valor": [fixed_total, variable_total, simulate_future_cost]
    })
    if breakdown["valor"].sum() <= 0:
        st.info("Adicione despesas para visualizar o gráfico.")
    else:
        pie = px.pie(breakdown, names="categoria", values="valor", title="Proporção de despesas", hole=0.4)
        pie.update_layout(margin=dict(t=30,b=0,l=0,r=0), legend=dict(orientation="h"))
        st.plotly_chart(pie, use_container_width=True)

st.markdown("---")

st.subheader("Projeção de saldo futuro (atualiza em tempo real)")
proj_df = projection_series(start_balance - simulate_future_cost, monthly_income, fixed_total, variable_total, months)
bar = px.bar(proj_df, x="month", y="balance", title="Projeção mensal do saldo", text="balance")
bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
bar.update_layout(yaxis_title="Saldo (R$)", xaxis_title="Mês", margin=dict(t=40))
st.plotly_chart(bar, use_container_width=True)

st.markdown("---")
st.subheader("Resumo da projeção")
st.dataframe(proj_df.style.format({"balance":"R$ {:,.2f}"}), height=260)

st.markdown("---")
final_balance = proj_df["balance"].iloc[-1] if not proj_df.empty else start_balance
if final_balance < 0:
    st.error(f"Projeção negativa no final do período: R$ {final_balance:,.2f}. Considere reduzir despesas ou aumentar receitas.")
else:
    st.success(f"Projeção saudável no final do período: R$ {final_balance:,.2f}.")
st.markdown("---")
st.caption("Aplicação demonstrativa com persistência SQLite e histórico de projeções.")