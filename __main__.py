from flask import Flask, request
import json
import requests
import os
import logging
import sys
import threading
from datetime import datetime

app = Flask(__name__)

@app.route('/<project>', methods=['POST'])
def deploy_project(project):
    filename = get_request_file()
    log_request_data(request, filename)
    try:
        json_data = request.json
        secret = json_data['hook']['config']['secret']
    except Exception as e:
        log.error('Error: {}'.format(e))
        return json.dumps({'error': 'Error: {}'.format(e)})
    if secret != conf['secret']:
        log.error('Invalid secret')
        return json.dumps({'error': 'Invalid secret'})
    log.info("Received request for project %s", project)
    log.info("Logged request data to file %s", filename)
    if project not in conf['projects']:
        log.error("Project %s not found", project)
        return json.dumps({'error': 'Project not found'}), 404
    directory = conf['projects'][project].get('directory')
    if not directory:
        log.error("Key 'directory' is not present in the "
                  "configuration for project %s", project)
        return json.dumps({'error': 'Bad project configuration'}), 500
    log.info('Deploying project {} to {}'.format(project, directory))
    job_id_command = ' | '.join([
        'ps ax',
        'grep "python {}"'.format(project),
        'grep -v grep',
        "grep -Po '^ *[0-9]+'"])
    log.info("Job ID command: %s", job_id_command)
    job_id = os.popen(job_id_command).read().strip()
    log.info("Job ID: %s", job_id)
    pull_and_restart_command = 'cd {} && git pull && kill {}'.format(
        directory, job_id)
    log.info("Pull and restart command: %s", pull_and_restart_command)
    exit_code = os.system(pull_and_restart_command)
    if exit_code == 0:
        log.info('Deployed project {} to {}'.format(project, directory))
        return json.dumps({
            'status': 'success',
            'message': 'Pulled latest from {} master'.format(project)
        })
    else:
        return json.dumps({'status': 'failed'}), 500

def good_bye():
    exit()


def get_request_file():
    timestamp = round(datetime.utcnow().timestamp(), 2)
    return os.path.join(log_directory, 'z-{}.log'.format(timestamp))

def log_request_data(request, filename):
    with open(filename, 'w') as f:
        json.dump(request.json, f, indent=2)

def load_configuration():
    conf_file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'config.json')
    log_directory = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'log')
    log_file = os.path.join(log_directory, 'deploy.log')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    with open(conf_file) as f:
        configuration = json.load(f)
    return configuration, log_directory, log_file


def setup_logging():
    logger = logging.getLogger("deploy")
    logger.setLevel(logging.INFO)
    stdout_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    stdout_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    (conf, log_directory, log_file) = load_configuration()
    log = setup_logging()
    app.secret_key = os.urandom(12)
    log.info("Starting deploy server")
    app.run(
        host=conf['host'],
        port=conf['port'],
        debug=conf['debug'])
