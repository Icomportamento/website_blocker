import psycopg2

def get_conn():
    return psycopg2.connect(
            dbname="teste_smart",
            user="postgres",
            password="iransneto",
            host="147.79.107.87",
            port="5432"
        )
    
