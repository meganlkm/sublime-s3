import boto3
import jmespath
import sublime
import sublime_plugin


class Buckets(object):

    def __init__(self):
        s3 = boto3.client('s3')
        self.buckets = jmespath.search('Buckets[*].Name', s3.list_buckets())

    def get(self, index):
        return self.buckets.index(index)

    def list(self):
        self.buckets.sort()
        return self.buckets


class S3EditorCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.status_message('Doing the S3 Editor Thing')


class ListBuckets(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().show_quick_panel(
            self.list(),
            self.list_objects
        )

    def list(self):
        return Buckets().list()

    def list_objects(self, thing):
        status = [
            'thing: {}'.format(str(thing))
        ]

        panel = sublime.active_window().new_file()
        panel.set_name("Foo")
        panel.set_scratch(True)
        panel.run_command('append', {'characters': '\n'.join(status)})
