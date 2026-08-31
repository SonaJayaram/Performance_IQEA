import configparser
import psycopg2
from cryptography.fernet import Fernet

DB_config = configparser.ConfigParser()
DB_config.read('DBconfig.ini')

def getvaluefromdatabse(sql_query):
    # Database connection parameters
    f = Fernet(DB_config.get('DBconfig', 'key'), )
    db_params = {
        'host': DB_config.get('DBconfig', 'localhost'),
        'port': DB_config.get('DBconfig', 'port'),
        'database': DB_config.get('DBconfig', 'database'),
        'user': f.decrypt(DB_config.get('DBconfig', 'en_user_name')).decode(),
        'password': f.decrypt(DB_config.get('DBconfig', 'en_password')).decode(),
    }
    # Establish a connection to the PostgreSQL database
    try:
        connection = psycopg2.connect(**db_params)
        # Create a cursor object to interact with the database
        cursor = connection.cursor()
        # Execute the SQL query
        cursor.execute(sql_query)
        # Fetch the first value from the query result
        value = cursor.fetchone()[0]  # Assuming the query returns one value
        return value
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL:", error)
        return None
    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed.")