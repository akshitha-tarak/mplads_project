import pandas as pd
import os

folder = "data/cleaned"

for file in os.listdir(folder):

    print("\n" + "="*80)
    print(file)
    print("="*80)

    df = pd.read_csv(os.path.join(folder, file))

    print(df.columns.tolist())