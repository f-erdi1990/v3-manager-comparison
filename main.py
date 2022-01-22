import os
import json
import pandas as pd

import query
import helper

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'query_config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("log: config file not found")


def save_df(df):
    """takes a dataframe as an argument and saves it somewhere or so"""
    spreadsheet = helper.Sheets("v3-optimizer-data")
    old_df = spreadsheet.get_df()
    if not old_df.empty:
        new_df = pd.concat([old_df, df])
    else:
        new_df = df

    new_df = new_df.convert_dtypes()
    spreadsheet.write_df(new_df)
    print("log: new dataframe written into google spreadsheet: {}".format(spreadsheet.sheet_name))
    return

def main():
    df = query.Query(config).compile()
    save_df(df)
    return


# execute script
if __name__ == '__main__':
    main()
