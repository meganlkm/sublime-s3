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
        self.objects = None
        self.keys = None

        self.resource = boto3.resource('s3')
        self.client = boto3.client('s3')

        # TODO cache this...
        self.bucket = self.resource.Bucket(bucket)
        self.set_objects()

    def set_objects(self):
        self.objects = self.bucket.objects.all()
        if self.objects:
            self.keys = [o.key for o in self.objects]
            self.keys.sort()

    def get(self, index):
        try:
            return self.keys[index]
        except IndexError:
            panel = sublime.active_window().new_file()
            panel.set_name("Error")
            panel.set_scratch(True)
            panel.run_command(
                'append', {
                    'characters': 'index ({}) not found in {}'.format(str(index), self.bucket.name)
                }
            )

    def list(self):
        if self.keys:
            return self.keys
        return ['{} does not have any objects'.format(self.bucket.name)]


class S3EditorCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.buckets = Buckets()
        self.bucket = None

        sublime.active_window().show_quick_panel(
            self.buckets.list(),
            self.list_objects
        )

    def list_objects(self, bucket_index):
        self.bucket = self.buckets.get(bucket_index)
        self.objects = Objects(self.bucket)
        sublime.active_window().show_quick_panel(
            self.objects.list(),
            self.display
        )

    def display(self, key_index):
        key = self.objects.get(key_index)
        status = [
            'key_index: {}'.format(str(key_index)),
            'key: {}'.format(key),
            '',
            '-' * 79,
            ''
        ]

        panel = sublime.active_window().new_file()
        panel.set_name(key)
        panel.set_scratch(True)
        panel.run_command('append', {'characters': '\n'.join(status)})
