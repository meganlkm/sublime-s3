import boto3
import jmespath
import sublime
import sublime_plugin


class State(object):

    def __init__(self):
        self.profile = None
        self.bucket = None


STATE = State()


class Profile(object):

    def __init__(self):
        self.profiles = None
        self.session = boto3.session.Session()
        self.set_available_profiles()

    def set_available_profiles(self):
        try:
            self.profiles = self.session.available_profiles
        except AttributeError:
            try:
                self.profiles = self.session._session.available_profiles
            except AttributeError:
                # no profiles?
                self.profiles = []
        self.profiles.sort()

    def get(self, index):
        return self.profiles[index]

    def list(self):
        return self.profiles


class S3ProfileSelectorCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.profile_obj = Profile()
        sublime.active_window().show_quick_panel(
            self.profile_obj.list(),
            self.set_profile
        )

    def set_profile(self, index):
        STATE.profile = self.profile_obj.get(index)
        sublime.status_message('AWS profile set: {}'.format(STATE.profile))


class S3SelectedProfileCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.status_message('AWS profile: {}'.format(STATE.profile))


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
        objects = self.bucket.objects.all()
        if objects:
            self.keys = [o.key for o in objects]
            self.keys.sort()
            self.objects = dict([(o.key, o) for o in objects])

    def get(self, key):
        try:
            return self.objects[key]
        except KeyError:
            sublime.error_message('key ({}) not found in {}'.format(key, self.bucket.name))

    def get_key(self, index):
        try:
            return self.keys[index]
        except IndexError:
            sublime.error_message('index ({}) not found in {}'.format(str(index), self.bucket.name))

    def list(self):
        if self.keys:
            return self.keys
        sublime.error_message('{} does not have any objects'.format(self.bucket.name))


class S3Editor(sublime_plugin.WindowCommand):

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
        key = self.objects.get_key(key_index)
        obj = self.objects.get(key)
        doc = obj.get()
        content = doc['Body'].read()

        panel = sublime.active_window().new_file()
        panel.set_name(key)
        panel.set_scratch(True)
        panel.run_command('append', {'characters': content})
