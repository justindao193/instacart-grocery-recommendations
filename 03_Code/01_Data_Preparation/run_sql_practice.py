# Load the Python tools used by this script.
from pathlib import Path
import duckdb
# Find the project folder so paths work from different starting locations.
ROOT=Path(__file__).resolve().parents[2]
# Open the database read-only; this exercise does not change any data.
with duckdb.connect(str(ROOT/'02_Data/02_Prepared/instacart.duckdb'),read_only=True) as con:
    # Run each practice query and print its result.
    for number,query in enumerate((ROOT/'03_Code/01_Data_Preparation/sql_practice.sql').read_text(encoding='utf-8').split(';'),start=1):
        if query.strip():
            print(f"\nExercise {number}")
            print(con.execute(query).df().to_string(index=False))
