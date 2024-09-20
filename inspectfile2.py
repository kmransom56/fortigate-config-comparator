import pandas as pd

# Define the file path
file_path = 'data.txt'

# Read the data using whitespace as the delimiter
df = pd.read_csv(file_path, delim_whitespace=True, skiprows=2)

# Display the DataFrame to verify the data and column names
print(df.head())
print(df.columns)