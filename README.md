# Application d'analyse statistique descriptive

Cette application Streamlit permet de définir des variables, de saisir des données en ligne et de réaliser une étude descriptive.

## Fonctionnalités

- Définition des variables :
  - Qualitative nominale
  - Qualitative ordinale
  - Quantitative discrète
  - Quantitative continue
- Saisie des observations ligne par ligne
- Affichage des effectifs pour les variables qualitatives
- Affichage des statistiques (moyenne, médiane, écart-type, quartiles, minimum, maximum) pour les variables quantitatives
- Visualisation simple avec des graphiques intégrés

## Installation

1. Crée un environnement Python :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Installe les dépendances :

```powershell
pip install -r requirements.txt
```

3. Lance l'application :

```powershell
streamlit run app.py
```

## Utilisation

1. Définis une variable et son type.
2. Ajoute toutes les variables nécessaires.
3. Saisis les observations.
4. Consulte les résultats descriptifs.

> Cette application est volontairement simple pour un travail d'étudiant de L2, mais elle reste robuste et facilement maintenable.
