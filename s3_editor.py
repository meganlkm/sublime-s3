import boto3
import jmespath
import sublime
import sublime_plugin


def list_bucket_objects(thing):
    status = [
        'Running list_buckets_callback...',
        'thing type: {}'.format(str(type(thing))),
        'thing: {}'.format(str(thing))
    ]

    # sublime.status_message(status)

    panel = sublime.active_window().new_file()
    panel.set_name("Foo")
    panel.set_scratch(True)
    panel.run_command('append', {'characters': '\n'.join(status)})

    # panel = sublime.active_window().create_output_panel('Foo')
    # panel.set_read_only(False)
    # panel.run_command('append', {'characters': status})
    # panel.set_read_only(True)

    # sublime.insert(edit, point, string)


class S3EditorCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sublime.status_message('Doing the S3 Editor Thing')


class ListBuckets(sublime_plugin.WindowCommand):

    def run(self):
        s3 = boto3.client('s3')
        self.buckets = jmespath.search('Buckets[*].Name', s3.list_buckets())
        sublime.active_window().show_quick_panel(
            self.list(),
            list_bucket_objects
        )

    def list(self):
        self.buckets.sort()
        return self.buckets
