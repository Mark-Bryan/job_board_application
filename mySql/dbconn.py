import mysql.connector


def get_db_conn():
    conn = mysql.connector.connect(
        host="localhost",
        user="Banyeh_Akika",
        password="#Capalot1900",
        database="job_listings",
    )
    return conn
