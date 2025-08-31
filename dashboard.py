# dashboard.py 

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

from dados_tratados import load_data

# 1) Config da página
st.set_page_config(
    page_title="Analise de Dados - CESAR School",
    page_icon="📈",
    layout="wide",
)

# 2) Logo centralizada
logo_path = Path(__file__).parent / "logo.png"
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
st.markdown("---")

# 3) Carregar dados tratados
@st.cache_data
def get_df():
    return load_data()

with st.spinner("Carregando dados..."):
    employee_df = get_df()

# 4) Validação de colunas
required = {"Gender", "PaymentTier"}
missing = required - set(employee_df.columns)
if missing:
    st.error(f"Colunas faltando: {sorted(missing)}")
    st.stop()

# 5) Padronizar Gender e manter Female/Male
employee_df = employee_df.copy()
employee_df["Gender"] = employee_df["Gender"].astype(str).str.strip().str.title()
employee_df = employee_df[employee_df["Gender"].isin(["Female", "Male"])]

# 6) Filtro por ano de ingresso (JoiningYear) — segmented control
if "JoiningYear" in employee_df.columns:
    employee_df["JoiningYear"] = pd.to_numeric(employee_df["JoiningYear"], errors="coerce").astype("Int64")
    year_opts = sorted([int(y) for y in employee_df["JoiningYear"].dropna().unique().tolist()])
    year_labels = ["Todos"] + [str(y) for y in year_opts]

    selected_year = st.segmented_control(
        "Selecione o ano de ingresso",
        options=year_labels,
        default="Todos"
    )

    if selected_year != "Todos":
        employee_df = employee_df[employee_df["JoiningYear"] == int(selected_year)]

    if employee_df.empty:
        st.warning("Não há dados para o ano selecionado.")
        st.stop()
else:
    st.info("Coluna **JoiningYear** não encontrada; filtro por ano indisponível.")

# 7) Tabela de percentuais PaymentTier × Gender
counts = employee_df.groupby(["PaymentTier", "Gender"]).size().unstack(fill_value=0)
row_sums = counts.sum(axis=1).replace(0, np.nan)
percent = counts.div(row_sums, axis=0).mul(100)

for g in ["Female", "Male"]:
    if g not in percent.columns:
        percent[g] = 0.0

percent = percent[["Female", "Male"]].fillna(0).round(1)
percent["Diferença (%)"] = (
    percent[["Female", "Male"]].max(axis=1) -
    percent[["Female", "Male"]].min(axis=1)
).round(1)

st.subheader("Insight 1 — Distribuição percentual por Nível de Pagamento e Gênero")
st.caption("Percentuais por PaymentTier × Gênero com filtro por ano de ingresso.")
st.dataframe(percent.reset_index().rename(columns={"PaymentTier": "Nível de Pagamento"}), use_container_width=True)

# 8) Gráfico 100% empilhado (Plotly)
order = sorted(percent.index.tolist())
plot_df = (
    percent[["Female", "Male"]]
      .reset_index()
      .melt(id_vars="PaymentTier", var_name="Gender", value_name="Percent")
)
plot_df["PaymentTier"] = pd.Categorical(plot_df["PaymentTier"], categories=order, ordered=True)

fig = px.bar(
    plot_df,
    x="PaymentTier",
    y="Percent",
    color="Gender",
    text="Percent",  
    title="Distribuição Percentual por Nível de Pagamento e Gênero",
    labels={"PaymentTier": "Nível de Pagamento", "Percent": "Percentual (%)"},
    height=450,     
)
fig.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="auto",   
    cliponaxis=False,      
)
fig.update_layout(
    barmode="stack",
    yaxis=dict(range=[0, 100]),
    legend_title_text="Gênero",
    uniformtext_minsize=10,   
    uniformtext_mode="show",  
    margin=dict(t=60, r=30, b=40, l=40),
)
st.plotly_chart(fig, use_container_width=True)




# ───────────────────────────────────────────────────────────────
# Insight 2 — Taxa de saída por experiência × EverBenched (PaymentTier selecionável)
# ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Insight 2 — Taxa de saída por experiência × EverBenched")

needed = {"PaymentTier", "LeaveOrNot", "EverBenched"}
missing = needed - set(employee_df.columns)
if missing:
    st.info(f"Para este insight, faltam as colunas: {sorted(missing)}")
else:
    # widget ----
    tiers_raw = employee_df["PaymentTier"].dropna().unique().tolist()
    # tenta ordenar numericamente; se não der, ordena por string...
    try:
        tiers_labels = [str(int(t)) for t in tiers_raw]
        tiers_labels = sorted(set(tiers_labels), key=lambda x: int(x))
    except Exception:
        tiers_labels = sorted([str(t) for t in tiers_raw])

    default_idx = tiers_labels.index("1") if "1" in tiers_labels else 0
    selected_label = st.selectbox("Escolha o PaymentTier", tiers_labels, index=default_idx)
    selected_tier = selected_label  

    # Base filtrada pelo tier escolhido
    base = employee_df[employee_df["PaymentTier"].astype(str) == str(selected_tier)].copy()
    if base.empty:
        st.warning("Sem dados para o PaymentTier selecionado após os filtros atuais.")
        st.stop()

    # coluna de experiência (ExpGrupo como padrao)
    exp_col = "ExpGrupo" if "ExpGrupo" in base.columns else "ExperienceInCurrentDomain"
    if exp_col not in base.columns:
        st.info("Coluna de experiência não encontrada (ExpGrupo ou ExperienceInCurrentDomain).")
    else:
        # Normalizar EverBenched -> 'No'/'Yes'
        ever_map = {
            "no": "No", "n": "No", "0": "No", "false": "No", "f": "No",
            "yes": "Yes", "y": "Yes", "1": "Yes", "true": "Yes", "t": "Yes",
        }
        base["EverBenched"] = (
            base["EverBenched"].astype(str).str.strip().str.lower().map(ever_map)
        )
        base = base[base["EverBenched"].isin(["No", "Yes"])]

        # Garantir LeaveOrNot numérico 0/1
        if not np.issubdtype(base["LeaveOrNot"].dtype, np.number):
            base["LeaveOrNot"] = (
                base["LeaveOrNot"].astype(str)
                .str.strip().str.lower()
                .map({"1": 1, "0": 0, "yes": 1, "no": 0, "true": 1, "false": 0})
            )
        base["LeaveOrNot"] = pd.to_numeric(base["LeaveOrNot"], errors="coerce")
        base = base.dropna(subset=["LeaveOrNot"])

        if base.empty:
            st.warning("Sem dados válidos para calcular a taxa de saída.")
            st.stop()

        # Tabela da taxa (média) por experiência × EverBenched
        taxa = (
            base.groupby([exp_col, "EverBenched"])["LeaveOrNot"]
                .mean()
                .unstack("EverBenched")
                .fillna(0)
                .sort_index()
        )

        # garantir as duas colunas (No/Yes)
        for c in ["No", "Yes"]:
            if c not in taxa.columns:
                taxa[c] = 0.0

        # remover linhas sem dados
        taxa = taxa[(taxa[["No", "Yes"]].sum(axis=1) > 0)].sort_index()

        if taxa.empty:
            st.warning("Sem dados suficientes para montar a tabela de taxas.")
            st.stop()

        # Tabela em %
        taxa_pct = (taxa * 100).round(1).rename_axis(index=exp_col).reset_index()
        taxa_pct = taxa_pct.rename(columns={"No": "Ocioso = Não", "Yes": "Ocioso = Sim"})
        st.caption(f"Taxa de saída (%) por experiência × EverBenched (PaymentTier = {selected_label})")
        st.dataframe(taxa_pct, use_container_width=True)

        # Plotly — barras agrupadas com rótulos dinâmicos
        plot_df = (
            taxa.reset_index()
                .melt(id_vars=exp_col, value_vars=["No", "Yes"],
                      var_name="EverBenched", value_name="Rate")
        )
        plot_df["EverBenched"] = plot_df["EverBenched"].map({"No": "Ocioso = Não", "Yes": "Ocioso = Sim"})

        fig2 = px.bar(
            plot_df,
            x=exp_col, y="Rate", color="EverBenched",
            barmode="group",
            title=f"Taxa de saída por experiência (PaymentTier = {selected_label})",
            labels={exp_col: "Experiência na mesma função", "Rate": "Taxa de saída"},
            text="Rate",
            height=450,
        )
        fig2.update_yaxes(range=[0, 1], tickformat=".0%")
        fig2.update_traces(
            texttemplate="%{y:.0%}",
            textposition="outside",   
            cliponaxis=False,         
            # width=0.35,             
        )
        fig2.update_layout(
            legend_title_text="EverBenched",
            uniformtext_minsize=10,
            uniformtext_mode="show",
            margin=dict(t=60, r=30, b=40, l=40),
        )

        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("📌 Como interpretar"):
            st.markdown(f"""
- Cada grupo de barras representa uma **faixa de experiência** ({exp_col}).
- Em cada faixa, comparamos **Ocioso = Não** vs **Ocioso = Sim**.
- O eixo Y mostra a **taxa de saída** (proporção de `LeaveOrNot = 1`).
- O seletor acima permite analisar **qualquer PaymentTier** (atual: **{selected_label}**).
""")

            

# ───────────────────────────────────────────────────────────────
# Insight 3 — Distribuição da Faixa Salarial (menor escolaridade) + FILTROS
# ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Insight 3 — Distribuição da Faixa Salarial para Funcionários com Menor Escolaridade")

needed = {"Education", "PaymentTier"}
missing = needed - set(employee_df.columns)
if missing:
    st.info(f"Para este insight, faltam as colunas: {sorted(missing)}")
else:
    base_all = employee_df.copy()

    
    # 1) Filtro por Gênero (segmented control)
    if "Gender" in base_all.columns:
        base_all["Gender_std"] = base_all["Gender"].astype(str).str.strip().str.title()
        g_choice = st.segmented_control(
            "Filtrar por gênero",
            options=["Todos", "Female", "Male"],
            default="Todos",
        )
        if g_choice != "Todos":
            base_all = base_all[base_all["Gender_std"] == g_choice]

    # 2) Filtro por EverBenched (Ocioso)
    if "EverBenched" in base_all.columns:
        ever_map = {
            "no": "No", "n": "No", "0": "No", "false": "No", "f": "No",
            "yes": "Yes", "y": "Yes", "1": "Yes", "true": "Yes", "t": "Yes",
        }
        base_all["EverBenched_std"] = (
            base_all["EverBenched"].astype(str).str.strip().str.lower().map(ever_map)
        )
        e_choice = st.segmented_control(
            "Filtrar por ociosidade (EverBenched)",
            options=["Todos", "Ocioso = Não", "Ocioso = Sim"],
            default="Todos",
        )
        if e_choice == "Ocioso = Não":
            base_all = base_all[base_all["EverBenched_std"] == "No"]
        elif e_choice == "Ocioso = Sim":
            base_all = base_all[base_all["EverBenched_std"] == "Yes"]

    # 3) Filtro por período de ingresso (JoiningYear)
    if "JoiningYear" in base_all.columns:
        base_all["JoiningYear_num"] = pd.to_numeric(base_all["JoiningYear"], errors="coerce").astype("Int64")
        years = base_all["JoiningYear_num"].dropna()
        if not years.empty:
            y_min, y_max = int(years.min()), int(years.max())
            if y_min == y_max:
                st.caption(f"Período de ingresso disponível: **{y_min}**")
            else:
                y_from, y_to = st.slider(
                    "Filtrar por ano de ingresso",
                    min_value=y_min, max_value=y_max,
                    value=(y_min, y_max), step=1,
                )
                base_all = base_all[base_all["JoiningYear_num"].between(y_from, y_to)]

    if base_all.empty:
        st.warning("Sem dados após aplicar os filtros.")
        st.stop()

    # -------------------- Preparação de Education --------------------
    # Education pode ser numérica (1=Bachelors, 2=Masters, 3=PHD) ou texto
    edu_map = {"Bachelors": 1, "Masters": 2, "PHD": 3}
    if not np.issubdtype(base_all["Education"].dtype, np.number):
        base_all["Education"] = base_all["Education"].replace(edu_map)
    base_all["Education"] = pd.to_numeric(base_all["Education"], errors="coerce")

    lowest_education = base_all["Education"].min()
    if pd.isna(lowest_education):
        st.warning("Não foi possível determinar a menor escolaridade na seleção atual.")
        st.stop()

    label_map = {1: "Bachelors", 2: "Masters", 3: "PHD"}
    edu_label = label_map.get(int(lowest_education), str(lowest_education))

    # Base final: somente menor escolaridade dentro do recorte filtrado
    base = base_all[base_all["Education"] == lowest_education].copy()
    if base.empty:
        st.warning("Não há registros para a menor escolaridade na seleção atual.")
        st.stop()

    # -------------------- Contagem por PaymentTier --------------------
    counts = (
        base["PaymentTier"]
        .value_counts(dropna=False)
        .rename_axis("PaymentTier")
        .sort_index()
        .reset_index(name="Quantidade")
    )
    counts["Percentual"] = counts["Quantidade"] / counts["Quantidade"].sum()

    st.caption(
        f"Escolaridade mínima **{edu_label}** | Registros: **{len(base)}** "
        f"| Faixas salariais distintas: **{counts['PaymentTier'].nunique()}**"
    )

    # Tabela 
    with st.expander("📊 Tabela de contagem e % por Faixa Salarial"):
        st.dataframe(
            counts.assign(Percentual=(counts["Percentual"] * 100).round(1)),
            use_container_width=True,
        )

    # -------------------- Gráfico de barras (contagem) --------------------
    fig3 = px.bar(
        counts,
        x="PaymentTier",
        y="Quantidade",
        text="Quantidade",
        title=f"Distribuição da Faixa Salarial — Escolaridade mínima: {edu_label}",
        labels={"PaymentTier": "Faixa Salarial", "Quantidade": "Número de Funcionários"},
        height=450,
    )
    # Mostrar % no hover e garantir rótulo sempre visível
    fig3.update_traces(
        hovertemplate="Faixa: %{x}<br>Qtd: %{y}<br>%: %{customdata:.1%}<extra></extra>",
        customdata=counts["Percentual"],
        textposition="outside",
        cliponaxis=False,
    )
    fig3.update_layout(
        uniformtext_minsize=10,
        uniformtext_mode="show",
        margin=dict(t=60, r=30, b=40, l=40),
    )

    st.plotly_chart(fig3, use_container_width=True)


