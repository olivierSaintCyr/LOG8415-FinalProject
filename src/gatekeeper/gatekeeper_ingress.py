from flask import Flask, request, jsonify, Response
import json
import requests

app = Flask(__name__)
CONFIG_FILE = 'config.json'

def load_config(config_path: str = CONFIG_FILE):
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config(config_path=CONFIG_FILE)

def is_body_valid(body: dict, path: str):
    body_fields = config['bodyFields'].get(path, [])
    if len(body_fields) == 0:
        return True
    
    for field in body.keys():
        if field not in body_fields:
            return False
    
    return True

def is_query_valid(query: str):
    forbiden_commands = config['forbidenCommands']
    for forbiden_command in forbiden_commands:
        if forbiden_command in query:
            return False
    
    return True

def validate_request(body: dict, path: str):
    if not is_body_valid(path=path, body=body):
        return 'INVALID_BODY', 400
    
    if path == '/query' and not is_query_valid(query=body['query']):
        return 'FORBIDEN_SQL_QUERY', 403
    
    return None, 200


@app.route('/', methods=["GET"])
@app.route('/mode', methods=['GET', 'PUT'])
@app.route('/query', methods=['POST'])
def redirect_to_trusted_host():
    trusted_host = config['trustedHostname']
    if request.method != 'GET':
        error, status_code = validate_request(
            body=request.get_json(),
            path=request.path,
        )
        if status_code != 200:
            return jsonify({ 'error': error } ), status_code

    res = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, f'http://{trusted_host}/'),
        headers={k:v for k,v in request.headers if k.lower() != 'host'}, # exclude 'host' header
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )
    
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']  #NOTE we here exclude all "hop-by-hop headers" defined by RFC 2616 section 13.5.1 ref. https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
    headers = [
        (k,v) for k,v in res.raw.headers.items()
        if k.lower() not in excluded_headers
    ]
    
    return Response(res.content, res.status_code, headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
