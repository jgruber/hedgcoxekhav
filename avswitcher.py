#!/usr/bin/env python3

import os
import sys
import signal
import json
import socket
import time
import subprocess
import datetime

from flask import Flask, request, jsonify, Response

CONFIG = {
    'WEB_SERVICE_PORT': 3100,
    'WEB_SERVICE_DEBUG': False,
    'AV_SWITCH_IP': '192.168.5.102',
    'AV_SWITCH_PORT': 7000,
    'AUDIO_MIXER_IP': '192.168.5.178',
    'DEFAULT_AUDIO_SCENE': {
        'file': 'Default.scn',
        'description': 'Default setting for public meetings'
    },
    'INIT_AUDIO_SCENE': {
        'file': 'Initialized.scn',
        'description': 'Scene used to initialize mixer settings'
    },
    'MUTE_SCENE': {
        'file': 'Mute.scn',
        'description': 'Mute all channel faders and sends'
    },
    'XAIRSETSCENE': '/usr/bin/XAirSetScene',
    'XAIRCMD': '/usr/bin/XAir_Command',
    'LIVELYNESS_CHECK_SECS': 2,
    'scenes': {}
}


DEFAULT_AUDIO_SCENE = ''
AUDIO_MIXER_INIT_SCENE = ''

DIFF = '/usr/bin/diff'
CUT = '/usr/bin/cut'
SED = '/bin/sed'

app = Flask('avswitcher')


last_scene = None
last_scene_loaded = None
last_audio_status = None
last_video_state = {}


@app.route('/status', methods=['GET'])
def return_last_status():
    ahost = CONFIG['AUDIO_MIXER_IP']
    if('host' in request.args):
        ahost = request.args.get('host')
    if not last_audio_status:
        get_audio_status(ahost)
    vhost = CONFIG['AV_SWITCH_IP']
    port = CONFIG['AV_SWITCH_PORT']
    if not last_video_state:
        query_av_state(vhost, port)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    object = {
        'timestamp': now,
        'last_scene': last_scene,
        'last_scene_loaded': last_scene_loaded,
        'last_video_state': last_video_state
    }
    return jsonify(object)


@app.route('/scene', methods=['POST'])
def scene_service():
    scene_data = request.json
    print('setting A/V scene %s' % json.dumps(scene_data))
    if 'videochannels' in scene_data:
        for ch in scene_data['videochannels']:
            set_av_state(
                CONFIG['AV_SWITCH_IP'], CONFIG['AV_SWITCH_PORT'], ch['input'], ch['output'])
    if 'audioscene' in scene_data:
        scene_found = False
        for scenename in CONFIG['scenes'].keys():
            if scene_data['audioscene'] == CONFIG['scenes'][scenename]['audioscene']:
                scene_found = True
                try:
                    set_audio_scene(CONFIG['AUDIO_MIXER_IP'], scenename)
                except Exception as e:
                    result = {'error': e.message}
                    return jsonify(result), 500
        if not scene_found:
            result = {
                'error': "no audio scene %s found" % scene_data['audioscene']}
            return jsonify(result), 404
    return jsonify({})


@app.route('/video', methods=['GET', 'POST'])
def video_service():
    host = CONFIG['AV_SWITCH_IP']
    port = CONFIG['AV_SWITCH_PORT']
    input = None
    output = None
    if request.method == 'POST':
        body = request.json()
        if ('input' in body and 'output' in body):
            if('host' in body):
                host = body.get('host')
            if('port' in body):
                port = body.get('port')
            input = body.get('input')
            output = body.get('output')
    else:
        if 'input' in request.args and 'output' in request.args:
            if('host' in request.args):
                host = request.args.get('host')
            if('port' in request.args):
                port = request.args.get('port')
            input = request.args.get('input')
            output = request.args.get('output')
    try:
        port = int(port)
    except:
        error = Exception('invalid port defined')
        error.status_code = 400
        raise error
    if(input and output):
        set_av_state(host, port, request.args.get(
            'input'), request.args.get('output'))
        time.sleep(1)
        return query_av_state(host, port)
    else:
        return query_av_state(host, port)


@app.route('/audio', methods=['GET', 'POST'])
def audio_service():
    host = CONFIG['AUDIO_MIXER_IP']
    scene = CONFIG['DEFAULT_AUDIO_SCENE']
    if request.method == 'POST':
        body = request.json()
        if('host' in body):
            host = body.get('host')
        if ('scene' in body):
            scene = body.get('scene')
        mute_audio(host)
        return set_audio_scene(host, scene)
    else:
        if('host' in request.args):
            host = request.args.get('host')
        if('scene' in request.args):
            scene = request.args.get('scene')
            mute_audio(host)
            return set_audio_scene(host, scene)
        else:
            return get_audio_status(host)


@app.route('/config', methods=['GET'])
def config_service():
    return jsonify(CONFIG)


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def catch_all(path):
    return app.send_static_file(path)


def query_av_state(host, port):
    global last_video_state
    avm = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    avm.settimeout(5)
    avm.connect((host, port))
    query_state = bytes.fromhex('a56c140082010100000000000000000053fc01ae')
    avm.send(query_state)
    current_state = avm.recv(100)
    current_state = current_state[18:26].strip()
    outputs = {}
    for indx, ch in enumerate(current_state):
        outputs[str(indx + 1)] = '%s' % ch
    last_video_state = {'outputs': outputs}
    return jsonify({'outputs': outputs})


def set_av_state(host, port, input, output):
    avm = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    avm.connect((host, port))
    cmd = "%sv%s." % (input, output)
    print("sending cmd: %s to %s:%d" % (cmd, host, port))
    avm.send(cmd.encode())


def initialize_audio_scene():
    global last_scene, last_scene_loaded
    host = CONFIG['AUDIO_MIXER_IP']
    initfile = "%s/static/audioscenes/%s" % (os.path.dirname(
        os.path.realpath(__file__)), CONFIG['INIT_AUDIO_SCENE']['file'])
    cmd = "cat %s | %s -i %s" % (
        initfile, CONFIG['XAIRSETSCENE'], host
    )
    print('sending cmd: %s' % cmd)
    FNULL = open(os.devnull)
    exitcode = subprocess.call(
        cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    if exitcode != 0:
        error = Exception(
            "could not set initialization scene - exit code %s" % exitcode)
        error.status_code = 500
        raise error
    else:
        defaultscenefile = "%s/static/audioscenes/%s" % (os.path.dirname(
            os.path.realpath(__file__)), CONFIG['DEFAULT_AUDIO_SCENE']['file'])
        cmd = "cat %s | %s -i %s" % (
            defaultscenefile, CONFIG['XAIRSETSCENE'], host
        )
        print('sending cmd: %s' % cmd)
        FNULL = open(os.devnull)
        exitcode = subprocess.call(
            cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
        if exitcode != 0:
            error = Exception(
                "could not set default scene %s - exit code %s" % exitcode)
            error.status_code = 500
            raise error
        else:
            last_scene_loaded = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            last_scene = 'Default'
            return jsonify({'scene': CONFIG['DEFAULT_AUDIO_SCENE']['file']})


def mute_audio(host):
    mutescenefile = "%s/static/audioscenes/%s" % (os.path.dirname(
        os.path.realpath(__file__)), CONFIG['MUTE_SCENE']['file'])
    cmd = "cat %s | %s -i %s" % (
        mutescenefile, CONFIG['XAIRSETSCENE'], host
    )
    print('sending cmd: %s' % cmd)
    FNULL = open(os.devnull)
    exitcode = subprocess.call(
        cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    if exitcode != 0:
        error = Exception(
            "could not mute audio - exit code %s" % exitcode)
        error.status_code = 500
        raise error


def set_audio_scene(host, scene):
    global last_scene, last_scene_loaded
    scenefile = "%s/static/audioscenes/%s" % (os.path.dirname(
        os.path.realpath(__file__)), CONFIG['scenes'][scene]['file'])
    cmd = "cat %s | %s -i %s" % (
        scenefile, CONFIG['XAIRSETSCENE'], host
    )
    print('sending cmd: %s' % cmd)
    FNULL = open(os.devnull)
    exitcode = subprocess.call(
        cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    if exitcode != 0:
        error = Exception(
            "could not set scene %s - exit code %s" % (scene, exitcode))
        error.status_code = 500
        raise error
    else:
        last_scene_loaded = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_scene = scene
        return jsonify({'scene': scene})


def set_audio_scene_init_diff(host, scene):
    global last_scene, last_scene_loaded
    scenefile = "%s/static/audioscenes/%s" % (os.path.dirname(
        os.path.realpath(__file__)), CONFIG['scenes'][scene]['file'])
    initfile = "%s/static/audioscenes/%s" % (os.path.dirname(
        os.path.realpath(__file__)), CONFIG['INIT_AUDIO_SCENE']['file'])
    cmd = "%s -y --suppress-common %s %s | %s -d'|' -f1 | %s 's/[[:space:]]*$//' | %s -i %s" % (
        DIFF, scenefile, initfile, CUT, SED, CONFIG['XAIRSETSCENE'], host)
    print('sending cmd: %s' % cmd)
    FNULL = open(os.devnull)
    exitcode = subprocess.call(
        cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    if exitcode != 0:
        error = Exception(
            "could not set scene %s - exit code %s" % (scene, exitcode))
        error.status_code = 500
        raise error
    else:
        last_scene_loaded = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_scene = scene
        return jsonify({'scene': scene})


def get_audio_status(host):
    bs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    bs.settimeout(5)
    bs.connect((host, 10024))
    bs.send(b"/status\n")
    current_state = bs.recv(100)
    current_state = current_state.decode()[16:].replace(
        '\x00', ' ').strip().split()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    outputs = {}
    outputs[current_state[1]] = {
        'status': current_state[0], 'name': current_state[2], 'polled': now}
    last_audio_status = now
    return jsonify({'outputs': outputs})


def load_config():
    global CONFIG
    config_file = "%s/config.json" % os.path.dirname(
        os.path.realpath(__file__))
    if os.path.exists(config_file):
        print('loading config from %s' % config_file)
        with open(config_file) as json_data_file:
            CONFIG = json.load(json_data_file)


if __name__ == '__main__':
    signal.signal(signal.SIGHUP, load_config)
    load_config()
    initialize_audio_scene()
    app.run(host='0.0.0.0',
            port=CONFIG['WEB_SERVICE_PORT'],
            debug=CONFIG['WEB_SERVICE_DEBUG'],
            threaded=True)
