import boto3
import jmespath
import sublime
import sublime_plugin


class Buckets(object):

    def __init__(self):
        self.s3 = boto3.client('s3')
        # TODO cache this list...
        self.buckets = jmespath.search(
            'Buckets[*].Name',
            self.s3.list_buckets()
        )
        self.buckets.sort()

    def get(self, index):
        return self.buckets[index]

    def list(self):
        return self.buckets


class Objects(object):

    def __init__(self, bucket):
        # TODO cache this...
        self.bucket = boto3.resource('s3').Bucket(bucket)
        self.objects = self.bucket.objects.all()
        self.keys = [o.key for o in self.objects]
        self.keys.sort()

    def get(self, index):
        return self.keys[index]

    def list(self):
        return self.keys


class S3EditorCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.status_message('Doing the S3 Editor Thing')


class ListBuckets(sublime_plugin.WindowCommand):

    def run(self):
        self.bucket = None
        sublime.active_window().show_quick_panel(
            self.list(),
            self.list_objects
        )

    def list(self):
        return Buckets().list()

    def list_objects(self, bucket_index):
        self.bucket = Buckets().get(bucket_index)
        sublime.active_window().show_quick_panel(
            Objects(self.bucket).list(),
            self.display
        )

    def display(self, key_index):
        key = Objects(self.bucket).get(key_index)
        status = [
            'key_index: {}'.format(str(key_index)),
            'key: {}'.format(key)
        ]
        panel = sublime.active_window().new_file()
        panel.set_name("S3 Key")
        panel.set_scratch(True)
        panel.run_command('append', {'characters': '\n'.join(status)})
