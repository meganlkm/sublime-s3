# S3 Things

A Plugin for doing things with files saved on AWS S3.

* [Commands](#commands)
* [TODO](#todo)

---

## <a name="commands"></a> Commands

### Session

#### Set Profile

Default: `default`

Select a profile defined in `~/.aws/credentials`.

#### Selected Profile

Show the active profile in the status bar.

### Buckets

#### Create Bucket

Create a new bucket in the active profile.

#### Set Bucket

Select a bucket available in the profile.

#### Selected Bucket

Show the active bucket in the status bar.

### Keys

#### Open File

Select and open a file that is uploaded to the selected bucket.


## <a name="todo"></a> TODO

* upload a file
* download a file
* escaping s3 key selection creates a new scratch file
* region selection
