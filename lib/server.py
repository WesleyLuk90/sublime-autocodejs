import subprocess
from os import path
import os
import json
import threading
import queue


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
        print("Starting autocodejs in %s" % path)
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
        self.queue = queue.Queue()
        self.start()

    def get_program_path(self):
        directory = path.dirname(path.dirname(__file__))
        program_path = path.join(directory, "autocodejs/build/main.js")
        return program_path

    def read_line(self, contents):
        if '\n' in contents:
            line, _, contents = contents.partition('\n')
            return line, contents
        return None, contents

    def stdout_reader(self):
        contents = ""
        while not self.process.poll():
            contents += os.read(self.process.stdout.fileno(), 2**15).decode('utf-8')
            line, contents = self.read_line(contents)
            if line:
                self.queue.put(line)

    def stderr_reader(self):
        contents = ""
        while not self.process.poll():
            contents += str(os.read(self.process.stderr.fileno(), 2**15))
            line, contents = self.read_line(contents)
            if line:
                print (line)

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
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)

        threading.Thread(target=self.stdout_reader).start()
        threading.Thread(target=self.stderr_reader).start()

    def close(self):
        self.process.terminate()

    def send_request(self, command_object):
        command = json.dumps(command_object) + "\n"
        bytes_written = self.process.stdin.write(command)
        if bytes_written != len(command):
            raise Exception("Not all bytes written")
        self.process.stdin.flush()
        response_content = self.queue.get(timeout=10)
        response = json.loads(response_content)
        return response

    def get_imports(self, path):
        response = self.send_request({'action': 'listImports', 'path': path})
        return response

    def get_insert_point(self, file_contents):
        response = self.send_request({'action': 'getInsertPoint', 'contents': file_contents})
        return response['insertPoint']


def main():
    instance = InstanceManager.get_instance('C:\\Users\\wesleyluk\\AppData\\Roaming\\Sublime Text 3\\Packages\\sublime-autocodejs')
    print ("Requesting")
    print(instance.get_imports('C:\\Users\\wesleyluk\\Desktop\\manga-reader\\src\\app\\sites\\sites.js'))
    print ("WE got a reply")
    print ("Got data Requesting")
    print(instance.get_imports('C:\\Users\\wesleyluk\\Desktop\\manga-reader\\src\\app\\sites\\sites.js'))
    print ("WE got a reply")
    print("Done")


if __name__ == '__main__':
    main()
