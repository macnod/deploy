from flask import Flask, request
import json
import requests
import os

app = Flask(__name__)

@app.route('/<project>', methods=['POST'])
def deploy_project(project):
    if project not in conf['projects']:
        return json.dumps({'error': 'Project not found'}), 404
    directory = conf['projects'][project]['directory']
    print('Deploying project {} to {}'.format(project, directory))
    print('Request data: {}'.format(request.data))
    if project == 'soothsayer':
        exit_code = os.system('cd {} && git pull'.format(directory))
        if exit_code == 0:
            return json.dumps({
                'status': 'success',
                'message': 'Pulled latest from {} master'.format(project)
            })
        else:
            return json.dumps({'status': 'failed'}), 500
    else:
        return json.dumps({'status': 'unknown project'}), 404
            

def load_configuration():
    conf_file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'config.json')
    with open(conf_file) as f:
        configuration = json.load(f)
    return configuration


if __name__ == '__main__':
    conf = load_configuration()
    app.secret_key = os.urandom(12)
    app.run(host=conf['host'], port=conf['port'], debug=conf['debug'])


