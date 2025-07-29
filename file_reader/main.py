import pandas as pd

def read_csv_file(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df




