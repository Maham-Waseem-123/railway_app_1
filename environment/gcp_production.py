import os

DATABASE_URI = "{db_connector}://{db_user_name}:{db_password}@/{db_name}?unix_sock={unix_socket_path}/.s.PGSQL.{db_port}".format(
    db_connector=os.environ.get('DB_CONNECTOR'),
    db_user_name=os.environ.get('DB_USER_NAME'),
    db_password=os.environ.get('DB_PASSWORD'),
    db_name=os.environ.get('DB_NAME'),
    unix_socket_path=os.environ.get('INSTANCE_UNIX_SOCKET'),
    db_port=os.environ.get('DB_PORT'))
