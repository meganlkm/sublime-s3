import boto3
import jmespath
import sublime
import sublime_plugin
from botocore.exceptions import ClientError


class Session(object):

    def __init__(self):
        self.bucket = None
        self.client = None
        self.profile_name = 'default'
        self.profiles = None
        self.region_name = None
        self.regions = None
        self.resource = None
        self.session = None
        self.set_profile(self.profile_name)

    def __set_session(self):
        kwargs = {'profile_name': self.profile_name}
        if self.region_name:
            kwargs['region_name'] = self.region_name
        self.session = boto3.session.Session(**kwargs)

    def __set_available_profiles(self):
        try:
            self.profiles = self.session.available_profiles
        except AttributeError:
            try:
                self.profiles = self.session._session.available_profiles
            except AttributeError:
                # no profiles?
                self.profiles = []
        self.profiles.sort()

    def __set_available_regions(self):
        self.regions = self.session.get_available_regions('s3')
        self.regions.sort()

    def get_profile(self, index):
        return self.profiles[index]

    def list_profiles(self):
        return self.profiles

    def set_profile(self, profile_name, region_name=None):
        self.profile_name = profile_name
        self.region_name = region_name
        self.__set_session()
        self.client = self.session.client('s3')
        self.resource = self.session.resource('s3')
        if not self.profiles:
            self.__set_available_profiles()
        if not self.regions:
            self.__set_available_regions()
        if not self.region_name:
            self.region_name = self.session.region_name

    def profile_state(self):
        sublime.status_message('AWS Profile: {}'.format(self.profile_name))

    def list_regions(self):
        return self.regions

    def get_region(self, index):
        return self.regions[index]

    def show_region(self):
        sublime.status_message('AWS Region: {}'.format(self.region_name))

    def set_bucket(self, bucket_name):
        self.bucket = bucket_name

    def bucket_state(self):
        sublime.status_message('AWS Selected Bucket: {}'.format(self.bucket))


STATE = Session()


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

        self.bucket_name = bucket
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

    def upload(self, filename, key):
        STATE.resource.Object(self.bucket_name, key).upload_file(filename)
        sublime.status_message('AWS Uploaded File: s3://{}/{}'.format(self.bucket, key))


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


class S3RegionSelectorCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().show_quick_panel(
            STATE.list_regions(),
            self.set_region
        )

    def set_region(self, index):
        STATE.set_profile(STATE.profile_name, STATE.get_region(index))
        STATE.show_region()


class S3SelectedRegionCommand(sublime_plugin.WindowCommand):

    def run(self):
        STATE.show_region()


class S3BucketSelectorCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.buckets = Buckets()
        sublime.active_window().show_quick_panel(
            self.buckets.list(),
            self.set_bucket
        )

    def set_bucket(self, bucket_index):
        STATE.set_bucket(self.buckets.get(bucket_index))
        STATE.bucket_state()


class S3CreateBucketCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        v = self.view
        v.window().show_input_panel('Bucket Name', '', self.create_bucket, None, None)

    def create_bucket(self, bucket_name):
        try:
            STATE.client.create_bucket(Bucket=bucket_name)
            sublime.status_message('Bucket Created: {}'.format(bucket_name))
        except ClientError as e:
            sublime.error_message('Error: {}'.format(str(e)))


class S3SelectedBucketCommand(sublime_plugin.WindowCommand):

    def run(self):
        STATE.bucket_state()


class S3OpenFileCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.objects = Objects(STATE.bucket)
        sublime.active_window().show_quick_panel(
            self.objects.list(),
            self.display
        )

    def display(self, key_index):
        key = self.objects.get_key(key_index)
        obj = self.objects.get(key)
        doc = obj.get()
        content = doc['Body'].read().decode("utf-8")

        panel = sublime.active_window().new_file()
        panel.set_name(key)
        panel.set_scratch(True)
        panel.run_command('append', {'characters': content})


class S3UploadFileCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.objects = Objects(STATE.bucket)
        win_vars = self.view.window().extract_variables()
        self.objects.upload(win_vars.get('file'), win_vars.get('file_name'))
