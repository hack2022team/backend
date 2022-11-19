import sqlite3
import pandas as pd

def write_to_database(info, escrow_wallet, appID):
    conn = sqlite3.connect('loans.sqlite')
    # conn.execute('''
    # create table if not exists loans
    # (
    #     id            INTEGER
    #         primary key autoincrement
    #         unique,
    #     name          TEXT    not null,
    #     email         TEXT    not null,
    #     story         TEXT    not null,
    #     location      TEXT    not null,
    #     wallet        TEXT    not null,
    #     escrow_wallet TEXT    not null,
    #     max_fees      INTEGER not null,
    #     sum           INTEGER not null,
    #     photo         BLOB    not null,
    #     risk          TEXT    not null,
    #     loan_duration INTEGER not null
    # )''')
    cursor = conn.cursor()
    sqlite_insert_with_param = """INSERT INTO loans
                      (name, email, story, location, wallet, escrow_wallet, max_fees, sum, photo, risk, loan_duration, status, appid) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

    data_tuple = (info['inputName'], info['inputEmail'], info['inputStory'], info['inputLocation'], info['inputWallet'], escrow_wallet,
                  info['inputMaxFees'], info['inputSum'], "", info['inputRisk'], info['inputDuration'], "OPEN", appID)
    cursor.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()
    conn.close()

def get_open_loans():
    conn = sqlite3.connect('loans.sqlite')
    open_loans = pd.read_sql_query("SELECT * from loans where status='OPEN'", conn)
    return open_loans.to_dict(orient="records")


def get_giver_accounts():
    conn = sqlite3.connect('loans.sqlite')
    open_loans = pd.read_sql_query("SELECT * from givers", conn)
    return open_loans.to_dict(orient="records")

def get_giver_key(key):
    conn = sqlite3.connect('loans.sqlite')
    open_loans = pd.read_sql_query("SELECT private_key from givers WHERE public_key='" + key +"'", conn)
    return open_loans.to_dict(orient="records")[0]['private_key']

def get_appid(key):
    conn = sqlite3.connect('loans.sqlite')
    open_loans = pd.read_sql_query("SELECT appid from loans WHERE escrow_wallet='" + key+"'", conn)
    return open_loans.to_dict(orient="records")[0]['appid']