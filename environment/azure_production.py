import os

DATABASE_URI = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}?sslmode=require'.format(
    db_connector='postgresql+psycopg2',
    dbuser=os.environ.get('DB_USER_NAME'),
    dbpass=os.environ.get('DB_PASSWORD'),
    dbhost=os.environ.get('DB_HOST'),
    dbport=os.environ.get('DB_PORT', 5432),  # Default PostgreSQL port
    dbname=os.environ.get('DB_NAME')
)