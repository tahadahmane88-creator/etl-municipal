import os
import glob
import re
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine


class BudgetMySQL_ETL:
    def __init__(self, input_directory: str, db_config: dict):
        self.input_dir = Path(input_directory)
        self.db_config = db_config

        # Mots-clés pour identifier l'en-tête du tableau dans chaque feuille
        self.keywords = {
            "الموارد المالية": "نوع المدخول المالي",
            "مصاريف التسيير": "نوع المصاريف",
            "مصاريف التجهيز": "نوع المصاريف"
        }

    def run_etl(self):
        master_data = {
            "revenues": [],
            "operating_expenses": [],
            "capital_expenses": []
        }

        # 1. Extract:
        excel_files = glob.glob(os.path.join(self.input_dir, "*.xlsx"))

        if not excel_files:
            print("❌ Aucun fichier Excel (.xlsx) trouvé dans le dossier !")
            return

        print(f"=== {len(excel_files)} fichier(s) Excel trouvé(s). Début de la conversion vers MySQL... ===")

        for file_path in excel_files:
            filename = os.path.basename(file_path)

            # Extraction de l'année (ex: 2024 ou 2025)
            year_match = re.search(r"(2024|2025)", filename)
            year = int(year_match.group(1)) if year_match else 0

            print(f"\n⚙️ Traitement de : {filename} (Année : {year})")

            xl = pd.ExcelFile(file_path)
            for sheet_name in xl.sheet_names:
                category_key = None
                if "الموارد المالية" in sheet_name or "المداخيل" in sheet_name:
                    category_key = "revenues"
                    keyword = self.keywords["الموارد المالية"]
                elif "مصاريف التسيير" in sheet_name or "التسيير" in sheet_name:
                    category_key = "operating_expenses"
                    keyword = self.keywords["مصاريف التسيير"]
                elif "مصاريف التجهيز" in sheet_name or "التجهيز" in sheet_name:
                    category_key = "capital_expenses"
                    keyword = self.keywords["مصاريف التجهيز"]

                if not category_key:
                    continue

                print(f"  -> Nettoyage de la feuille : {sheet_name}")

                # 2. Transform : Recherche de la ligne d'en-tête
                df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                header_row_idx = None
                for idx, row in df_raw.iterrows():
                    row_str = row.astype(str).values
                    if any(keyword in cell for cell in row_str if pd.notna(cell)):
                        header_row_idx = idx
                        break

                if header_row_idx is None:
                    continue

                df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_row_idx)

                # Nettoyage des en-têtes de colonnes (suppression des espaces pour MySQL)
                df.columns = [str(col).strip().replace(' ', '_').replace(' ', '_') for col in df.columns]
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                # Nettoyage des lignes et filtrage des valeurs non désirées
                mysql_keyword = keyword.replace(' ', '_').replace(' ', '_')
                if mysql_keyword in df.columns:
                    df = df[df[mysql_keyword].notna()]
                    df = df[~df[mysql_keyword].astype(str).str.contains(r'(ID\d|نوع)', case=False, na=False)]
                    # Suppression des lignes de total et des signatures pour éviter les doublons dans MySQL
                    keywords_to_drop = r'(المجموع|total|la somme|حرر|تأشيرة|رئيس جماعة)'
                    df = df[~df.astype(str).apply(lambda x: x.str.contains(keywords_to_drop, case=False, na=False)).any(
                        axis=1)]
                    df[mysql_keyword] = df[mysql_keyword].astype(str).str.replace(r'\xa0', ' ', regex=True).str.strip()

                # Conversion des montants financiers en valeurs numériques (Decimal/Float)
                id_pattern = re.compile(r'(ID\d|نوع|السنة|البيان)', re.IGNORECASE)
                numeric_cols = [col for col in df.columns if not id_pattern.search(col)]

                for col in numeric_cols:
                    df[col] = df[col].astype(str).str.replace(r'[^\d\.\-]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

                # Ajout des colonnes de traçabilité
                df['year_lineage'] = year
                df['budget_type'] = category_key

                master_data[category_key].append(df)

        # 3. Load : Chargement direct dans MySQL
        print("\n=== Phase 3: Loading Data Into MySQL ===")

        # Création de la connexion MySQL via SQLAlchemy
        # Format du DSN : mysql+mysqlconnector://user:password@host:port/database
        connection_string = f"mysql+mysqlconnector://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}?charset=utf8mb4"
        engine = create_engine(connection_string)

        for cat, dfs in master_data.items():
            if dfs:
                final_df = pd.concat(dfs, ignore_index=True)

                # Nom de la table dans MySQL
                table_name = f"municipal_{cat}"

                print(f"  -> Chargement de la table '{table_name}' dans MySQL ({len(final_df)} lignes)...")

                # Insertion des données (remplace la table si elle existe déjà)
                final_df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
                print(f"  ✅ Table '{table_name}' chargée avec succès dans MySQL !")

        print("\n🎉 Toutes les données ont été chargées avec succès dans MySQL !")


# --- Configuration de la connexion MySQL ---
if __name__ == "__main__":
    # ⚠️ Modifiez ces paramètres selon la configuration de votre serveur
    my_mysql_config = {
        "host": "localhost",  # ou l'adresse IP du serveur
        "port": "3306",  # Port par défaut de MySQL
        "user": "root",  # Nom d'utilisateur (ex: root pour XAMPP)
        "password": "",  # Mot de passe (laisser vide si aucun)
        "database": "suq_khamis_db"  # ⚠️ La base de données doit exister préalablement dans MySQL
    }

    # Exécution du pipeline
    # '.' indique que les fichiers Excel se trouvent dans le répertoire courant
    pipeline = BudgetMySQL_ETL(input_directory='.', db_config=my_mysql_config)
    pipeline.run_etl()