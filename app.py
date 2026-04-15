import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def initialize_state():
    """Initialise les états de session nécessaires."""
    if "variables" not in st.session_state:
        st.session_state["variables"] = []
    if "data_rows" not in st.session_state:
        st.session_state["data_rows"] = []
    if "message" not in st.session_state:
        st.session_state["message"] = ""


def reset_definitions():
    """Réinitialise les définitions de variables et les données saisies."""
    st.session_state["variables"] = []
    st.session_state["data_rows"] = []
    st.session_state["message"] = "Définitions et données réinitialisées."


def reset_data():
    """Réinitialise uniquement les données saisies, sans toucher aux définitions."""
    st.session_state["data_rows"] = []
    st.session_state["message"] = "Données effacées. Vous pouvez recommencer la saisie." 


def add_variable(name: str, vtype: str, categories: str):
    """Ajoute une variable à la définition du questionnaire."""
    name = name.strip()
    if not name:
        st.error("Le nom de la variable ne peut pas être vide.")
        return

    if any(var["name"].lower() == name.lower() for var in st.session_state["variables"]):
        st.error("Une variable avec ce nom existe déjà. Choisissez un autre nom.")
        return

    variable = {
        "name": name,
        "type": vtype,
        "categories": [cat.strip() for cat in categories.split(",") if cat.strip()] if categories else [],
    }
    st.session_state["variables"].append(variable)
    st.session_state["message"] = f"Variable '{name}' ajoutée." 


def format_variable_definition(variable: dict) -> str:
    """Retourne une chaîne de description d'une variable définition."""
    categories = ", ".join(variable["categories"]) if variable["categories"] else "(aucune)"
    return f"{variable['name']} — {variable['type']} — catégories: {categories}"


def add_data_row(row: dict):
    """Ajoute une nouvelle observation (ligne) aux données."""
    st.session_state["data_rows"].append(row)
    st.session_state["message"] = "Nouvelle ligne de données ajoutée." 


def build_dataframe():
    """Construit le DataFrame pandas à partir des données en session avec gestion d'erreurs."""
    if not st.session_state["data_rows"]:
        return pd.DataFrame()

    try:
        df = pd.DataFrame(st.session_state["data_rows"])
        for variable in st.session_state["variables"]:
            name = variable["name"]
            if variable["type"] in ["Qualitative nominale", "Qualitative ordinale"]:
                if variable["categories"]:
                    df[name] = pd.Categorical(df[name], categories=variable["categories"], ordered=(variable["type"] == "Qualitative ordinale"))
                else:
                    df[name] = df[name].astype("string")
            elif variable["type"] == "Quantitative discrète":
                try:
                    df[name] = pd.to_numeric(df[name], errors="coerce").astype("Int64")
                except Exception as e:
                    st.warning(f"Erreur lors de la conversion de '{name}' en entier : {str(e)}")
                    df[name] = pd.to_numeric(df[name], errors="coerce")
            elif variable["type"] == "Quantitative continue":
                try:
                    df[name] = pd.to_numeric(df[name], errors="coerce")
                except Exception as e:
                    st.warning(f"Erreur lors de la conversion de '{name}' en nombre décimal : {str(e)}")
        return df
    except Exception as e:
        st.error(f"Erreur lors de la construction du DataFrame : {str(e)}")
        return pd.DataFrame()


def export_to_csv(df: pd.DataFrame) -> str:
    """Exporte le DataFrame au format CSV."""
    return df.to_csv(index=False).encode('utf-8')


def compute_statistics(df: pd.DataFrame) -> dict:
    """Calcule un résumé statistique complet pour chaque variable."""
    summary = {}
    for variable in st.session_state["variables"]:
        name = variable["name"]
        if name not in df.columns or df[name].isna().all():
            continue

        if variable["type"] in ["Qualitative nominale", "Qualitative ordinale"]:
            counts = df[name].value_counts(dropna=False)
            rel = (counts / counts.sum()).round(3)
            mode = df[name].mode()
            summary[name] = {
                "type": variable["type"],
                "frequences": pd.DataFrame({"Fréquence": counts, "Fréquence relative": rel}),
                "mode": list(mode.astype(str)) if not mode.empty else [],
                "n": int(counts.sum()),
            }
        else:
            series = df[name].dropna().astype(float)
            if series.empty:
                continue
            description = series.describe()
            quartiles = series.quantile([0.25, 0.5, 0.75]).to_dict()
            q1 = quartiles[0.25]
            q3 = quartiles[0.75]
            iqr = q3 - q1
            etendue = description["max"] - description["min"]
            summary[name] = {
                "type": variable["type"],
                "count": int(description["count"]),
                "mean": float(round(description["mean"], 3)),
                "median": float(round(quartiles[0.5], 3)),
                "std": float(round(description["std"], 3)) if not np.isnan(description["std"]) else None,
                "min": float(round(description["min"], 3)),
                "max": float(round(description["max"], 3)),
                "etendue": float(round(etendue, 3)),
                "iqr": float(round(iqr, 3)),
                "quartiles": {"25%": float(round(q1, 3)), "50%": float(round(quartiles[0.5], 3)), "75%": float(round(q3, 3))},
                "missing": int(df[name].isna().sum()),
            }
    return summary


def display_summary(df: pd.DataFrame):
    """Affiche les statistiques descriptives et les visualisations optimisées."""
    if df.empty:
        st.info("Aucune donnée disponible pour analyse. Commencez par saisir des observations.")
        return

    st.subheader("Analyse descriptive")
    
    # Bouton de téléchargement CSV
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv_data,
        file_name="analyse_donnees.csv",
        mime="text/csv"
    )
    
    stats = compute_statistics(df)

    for variable in st.session_state["variables"]:
        name = variable["name"]
        if name not in stats:
            continue

        st.markdown(f"### {name} ({variable['type']})")
        
        if stats[name]["type"] in ["Qualitative nominale", "Qualitative ordinale"]:
            # Visualisations pour variables qualitatives
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Table des effectifs**")
                st.dataframe(stats[name]["frequences"], use_container_width=True)
                st.write(f"**Mode(s)** : {', '.join(stats[name]['mode'])}")
            
            with col2:
                # Diagramme en barres pour les fréquences absolues
                try:
                    fig_bar = px.bar(
                        x=stats[name]["frequences"].index,
                        y=stats[name]["frequences"]["Fréquence"],
                        labels={"x": name, "y": "Fréquence"},
                        title=f"Distribution des effectifs - {name}",
                    )
                    fig_bar.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                except Exception as e:
                    st.warning(f"Impossible d'afficher le graphique en barres : {e}")
            
            # Diagramme circulaire pour les fréquences relatives
            st.write("")
            try:
                fig_pie = px.pie(
                    values=stats[name]["frequences"]["Fréquence relative"],
                    names=stats[name]["frequences"].index,
                    title=f"Fréquences relatives (%) - {name}",
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            except Exception as e:
                st.warning(f"Impossible d'afficher le diagramme circulaire : {e}")
        
        elif variable["type"] == "Quantitative discrète":
            # Visualisations pour variables discrètes
            st.write("**Résumé statistique**")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Nombre", stats[name]["count"])
            col2.metric("Moyenne", stats[name]["mean"])
            col3.metric("Médiane", stats[name]["median"])
            col4.metric("Écart-type", stats[name]["std"] if stats[name]["std"] is not None else "N/A")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Min/Max/Étendue**")
                metrics_dict = {
                    "Minimum": stats[name]["min"],
                    "Maximum": stats[name]["max"],
                    "Étendue": stats[name]["etendue"],
                }
                st.write(metrics_dict)
            
            with col2:
                st.write("**Quartiles**")
                st.write(stats[name]["quartiles"])
            
            # Diagramme en bâtons pour variables discrètes
            try:
                value_counts = df[name].dropna().value_counts().sort_index()
                fig_stick = go.Figure()
                fig_stick.add_trace(go.Scatter(
                    x=value_counts.index.astype(str),
                    y=value_counts.values,
                    mode='markers+lines',
                    marker=dict(size=10, color='royalblue'),
                    line=dict(width=1),
                    name=name
                ))
                fig_stick.update_layout(
                    title=f"Diagramme en bâtons - {name}",
                    xaxis_title=name,
                    yaxis_title="Fréquence",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_stick, use_container_width=True)
            except Exception as e:
                st.warning(f"Impossible d'afficher le diagramme en bâtons : {e}")
        
        else:
            # Visualisations pour variables continues
            st.write("**Résumé statistique**")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Nombre", stats[name]["count"])
            col2.metric("Moyenne", stats[name]["mean"])
            col3.metric("Médiane", stats[name]["median"])
            col4.metric("Écart-type", stats[name]["std"] if stats[name]["std"] is not None else "N/A")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Min/Max/Étendue**")
                metrics_dict = {
                    "Minimum": stats[name]["min"],
                    "Maximum": stats[name]["max"],
                    "Étendue": stats[name]["etendue"],
                }
                st.write(metrics_dict)
            
            with col2:
                st.write("**Quartiles & IQR**")
                metrics_dict = {
                    **stats[name]["quartiles"],
                    "IQR": stats[name]["iqr"],
                }
                st.write(metrics_dict)
            
            # Histogramme avec règle de Sturges
            try:
                series = df[name].dropna().astype(float)
                n = len(series)
                k = int(1 + np.log2(n))  # Règle de Sturges
                
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=series,
                    nbinsx=k,
                    name=name,
                    marker_color='lightblue',
                    marker_line_color='darkblue',
                    marker_line_width=1
                ))
                fig_hist.update_layout(
                    title=f"Histogramme (Sturges: k={k}) - {name}",
                    xaxis_title=name,
                    yaxis_title="Fréquence",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            except Exception as e:
                st.warning(f"Impossible d'afficher l'histogramme : {e}")
            
            # Boîte à moustaches (Boxplot)
            try:
                series = df[name].dropna().astype(float)
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    y=series,
                    name=name,
                    boxmean='sd',
                    marker_color='indianred'
                ))
                fig_box.update_layout(
                    title=f"Boîte à moustaches - {name}",
                    yaxis_title=name,
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_box, use_container_width=True)
            except Exception as e:
                st.warning(f"Impossible d'afficher la boîte à moustaches : {e}")

        st.markdown("---")
    
    st.markdown("---")
    st.subheader("Aperçu des données brutes")
    st.dataframe(df, use_container_width=True)


def main():
    st.set_page_config(page_title="Analyse statistique en ligne", layout="wide")
    st.title("Application d'analyse statistique descriptive")
    st.write(
        "Cette application permet de définir des variables, de saisir des données ligne par ligne et d'obtenir un résumé descriptif. "
        "Elle accepte les variables qualitatives nominales, qualitatives ordinale, quantitatives discrètes et quantitatives continues."
    )

    initialize_state()

    # Colonne de gauche : définition des variables
    left, right = st.columns([1, 2])

    with left:
        st.header("1. Définir les variables")
        with st.form(key="variable_form"):
            var_name = st.text_input("Nom de la variable", placeholder="ex : Genre, Age, Niveau")
            var_type = st.selectbox(
                "Type de variable",
                ["Qualitative nominale", "Qualitative ordinale", "Quantitative discrète", "Quantitative continue"],
            )
            categories = ""
            if var_type in ["Qualitative nominale", "Qualitative ordinale"]:
                categories = st.text_input(
                    "Valeurs possibles (séparées par des virgules)",
                    placeholder="ex : Homme, Femme, Autre",
                )
            add_var = st.form_submit_button("Ajouter la variable")

        if add_var:
            add_variable(var_name, var_type, categories)

        if st.session_state["variables"]:
            st.write("Variables définies :")
            for var in st.session_state["variables"]:
                st.write(format_variable_definition(var))

        if st.button("Réinitialiser variables et données"):
            reset_definitions()

        if st.button("Effacer les données seulement"):
            reset_data()

        if st.session_state["message"]:
            st.success(st.session_state["message"])

    with right:
        st.header("2. Saisir les observations")
        if not st.session_state["variables"]:
            st.info("Définissez d'abord au moins une variable pour pouvoir saisir des données.")
        else:
            with st.form(key="data_form"):
                row = {}
                for variable in st.session_state["variables"]:
                    name = variable["name"]
                    vtype = variable["type"]
                    if vtype == "Qualitative nominale":
                        if variable["categories"]:
                            row[name] = st.selectbox(name, options=variable["categories"], key=f"input_{name}")
                        else:
                            row[name] = st.text_input(name, key=f"input_{name}")
                    elif vtype == "Qualitative ordinale":
                        if variable["categories"]:
                            row[name] = st.selectbox(name, options=variable["categories"], key=f"input_{name}")
                        else:
                            row[name] = st.text_input(name, key=f"input_{name}")
                    elif vtype == "Quantitative discrète":
                        row[name] = st.number_input(name, step=1, format="%d", key=f"input_{name}")
                    else:
                        row[name] = st.number_input(name, format="%f", key=f"input_{name}")
                add_row = st.form_submit_button("Ajouter l'observation")

            if add_row:
                add_data_row(row)

            st.write(f"Nombre d'observations : {len(st.session_state['data_rows'])}")
            if st.session_state["data_rows"]:
                recent = pd.DataFrame(st.session_state["data_rows"]).tail(10)
                st.write("Dernières observations saisies :")
                st.dataframe(recent)

    st.markdown("---")
    st.header("3. Résultats de l'étude descriptive")
    df = build_dataframe()
    display_summary(df)


if __name__ == "__main__":
    main()
