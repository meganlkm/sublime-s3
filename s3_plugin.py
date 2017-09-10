import boto3
import jmespath
import sublime
import sublime_plugin


class Session(object):

    def __init__(self):
        self.bucket = None
        self.client = None
        self.profile_name = None
        self.profiles = None
        self.resource = None

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

    def get_profile(self, index):
        return self.profiles[index]

    def list_profiles(self):
        return self.profiles

    def set_profile(self, profile_name):
        self.profile_name = profile_name
        self.session = boto3.session.Session(profile_name=profile_name)
        self.client = self.session.client('s3')
        self.resource = self.session.resource('s3')

    def profile_state(self):
        sublime.status_message('AWS Profile: {}'.format(self.profile_name))


STATE = Session()


class S3ProfileSelectorCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().show_quick_panel(
            STATE.list_profiles(),
            self.set_profile
        )

    def set_profile(self, index):
        STATE.set_profile(STATE.get_profile(index))
        STATE.profile_state()


class S3SelectedProfileCommand(sublime_plugin.WindowCommand):

    def run(self):
        STATE.profile_state()


class Buckets(object):

    def __init__(self):
        self.buckets = jmespath.search(
            'Buckets[*].Name',
            STATE.client.list_buckets()
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

        self.bucket = STATE.resource.Bucket(bucket)
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


class S3OpenFileCommand(sublime_plugin.WindowCommand):

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
