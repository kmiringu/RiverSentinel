import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

def train_riparian_material_classifier(training_csv_path, model_export_path):
    print("[step 2] Initializing Random Forest Material Engine...")

    # 1. Safety Check: verify training spreadsheet exists
    if not os.path.exists(training_csv_path):
        raise FileNotFoundError(
            f" Missing pixel training data! Please run previous files for export"
            f" the point-sampled spreadsheet to: {training_csv_path}"
        )

    # 2. Load point-sampled Table
    # Spreadsheet contains rows of pixels sampled from a clean image ribbon
    pixel_data = pd.read_csv(training_csv_path)
    print(f" Loaaded {len(pixel_data)} verified training pixel samples.")

    