import subprocess
from os import path
import json
from urllib.request import urlopen


def plugin_unloaded():
    InstanceManager.close_all()


class InstanceManager:
    instances_by_path = {}

    @classmethod
    def get_port(cls):
        return 61234

    @classmethod
    def get_instance(cls, path):
        if path not in cls.instances_by_path:
            cls.instances_by_path[path] = cls.create_instance(path)
        return cls.instances_by_path[path]

    @classmethod
    def create_instance(cls, path):
        return Runner(path, cls.get_port())

    @classmethod
    def close_all(cls):
        for instance in cls.instances_by_path.values():
            instance.close()
        cls.instances_by_path = {}


class Runner:
    def __init__(self, path, port):
        self.path = path
        self.port = port
        self.start()

    def get_program_path(self):
        directory = path.dirname(__file__)
        program_path = path.join(directory, "autocodejs/build/main.js")
        return program_path

    def start(self):
        args = [
            'node',
            self.get_program_path(),
            '--project-path',
            self.path,
            '--server',
            '--port',
            str(self.port)
        ]
        self.process = subprocess.Popen(args)
        # self.process = subprocess.Popen(args, shell=True)

    def close(self):
        self.process.terminate()

    def get_url(self):
        return "http://127.0.0.1:%s" % self.port

    def send_request(self, command_object):
        command = json.dumps(command_object)
        encoded = bytes(command.encode('utf-8'))
        connection = urlopen(self.get_url(), encoded)
        response = json.loads(connection.read().decode('utf-8'))
        return response

    def get_imports(self, path):
        response = self.send_request({'action': 'listImports', 'path': path})
        return response

    def get_insert_point(self, file_contents):
        response = self.send_request({'action': 'getInsertPoint', 'contents': file_contents})
        return response['insertPoint']
