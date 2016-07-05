import sublime
import sublime_plugin
from .lib import server
import imp


def plugin_unloaded():
    server.InstanceManager.close_all()
    imp.reload(server)


class ExitHandler(sublime_plugin.EventListener):
    def on_close(self, view):
        if not sublime.windows():
            plugin_unloaded()


class AutocodejsInsertImport(sublime_plugin.TextCommand):
    def run(self, edit, path=None, name=None, insert_point=None, module=False):
        if module:
            line = "\nimport %s from '%s';" % (name, path)
        else:
            line = "\nimport { %s } from '%s';" % (name, path)

        self.view.insert(edit, insert_point, line)


class AutocodejsResync(sublime_plugin.TextCommand):
    def run(self, edit):
        server.InstanceManager.close_all()


class AutocodejsListImports(sublime_plugin.TextCommand):

    def run(self, edit):
        first_folder = self.view.window().folders()[0]
        instance = server.InstanceManager.get_instance(first_folder)
        response = instance.get_imports(self.view.file_name())
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))

        items = []
        for file in response['importList']:
            for name in file['names']:
                items.append([name, file['path']])

        for module in response['modules']:
            items.append([module['name'], module['path']])

        def on_done(index):
            if index < 0:
                return
            item = items[index]
            insert_point = instance.get_insert_point(file_contents)
            if index < len(response['importList']):
                self.view.run_command('autocodejs_insert_import', {"path": item[1], "name": item[0], "insert_point": insert_point})
            else:
                self.view.run_command('autocodejs_insert_import', {"path": item[1], "name": item[0], "insert_point": insert_point, "module": True})

        self.view.window().show_quick_panel(items, on_done)
