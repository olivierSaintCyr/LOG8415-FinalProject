from flask import Flask, request, jsonify
from enum import Enum
import json
from sshtunnel import SSHTunnelForwarder
import paramiko
import pymysql
import os

app = Flask(__name__)

CONFIG_FILE = 'config.json'
SSH_HOST_NAME = 'ubuntu'
SSH_KEY_PATH = '../../final_project_gen_key.pem'

def load_config(config_path: str = CONFIG_FILE):
    with open(config_path, 'r') as f:
        return json.load(f)

class Proxy:
    class Mode(Enum):
        DIRECT_HIT = 0
        RANDOM = 1
        CUSTOMIZED = 2
    
    def __init__(self, config: dict, key_path=SSH_KEY_PATH) -> None:
        self.mode = Proxy.Mode.DIRECT_HIT
        self.hosts = config['sqlClusterHostnames']
        
        self.pkey = paramiko.RSAKey.from_private_key_file(key_path) # TODO add key to server
        self.execution = {
            Proxy.Mode.DIRECT_HIT: self.exec_direct_hit,
            Proxy.Mode.RANDOM: self.exec_random,
            Proxy.Mode.CUSTOMIZED: self.exec_customized,
        }

    def set_mode(self, mode: Mode):
        self.mode = mode
    
    def exec(self, query: str):
        return self.execution[self.mode](query)
    
    def execute_query(self, host, query):
        print('executing query on', host, query)
        print('key path', os.path.exists(SSH_KEY_PATH))
        with SSHTunnelForwarder(
            host,
            ssh_username=SSH_HOST_NAME,
            ssh_private_key=SSH_KEY_PATH,
            remote_bind_address=(self.hosts['master'], 3306),
            ssh_config_file=None,
            allow_agent=False,
        ) as tunnel:
            connection = pymysql.connect(
                host=self.hosts['master'],
                user='myapp1',
                password='testpwd',
                db='sakila',
                port=3306,
                autocommit=True
            )

            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                return cursor.fetchall()
            finally:
                connection.close()
            
        

    def exec_direct_hit(self, query):
        master_host = self.hosts['master']
        print('direct hit exec of', query)
        return self.execute_query(
            host=master_host,
            query=query
        )

    def exec_random(self, query):
        print('random exec of', query)

    def exec_customized(self, query):
        print('customized exec', query)

config = load_config()
proxy = Proxy(config=config)

@app.route('/')
def default():
    return '<h1>Hello World!</h1>'

@app.route('/mode', methods=['PUT'])
def change_mode():
    body = request.get_json()
    new_mode = Proxy.Mode[body['mode']]
    proxy.set_mode(new_mode)
    return jsonify(body)

@app.route('/mode', methods=['GET'])
def get_mode():
    return f'''<h1>Current mode: {proxy.mode.name}</h1>'''

@app.route('/query', methods=['POST'])
def exec_query():
    body = request.get_json()
    query = body['query']
    
    res = proxy.exec(query)
    
    return jsonify({
        'mode': proxy.mode.name,
        'result': res,
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
