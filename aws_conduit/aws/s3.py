import boto3

S3_RESOURCE = boto3.resource('s3')
S3_CLIENT = boto3.client('s3')


def create_bucket(name, region):
    bucket = S3_RESOURCE.Bucket(name)
    bucket.create(
        ACL='private',
        CreateBucketConfiguration={
            'LocationConstraint': region
        }
    )
    bucket.Versioning().enable()


def delete_bucket(name):
    bucket = S3_RESOURCE.Bucket(name)
    bucket.objects.all().delete()
    bucket.delete()


def get_sub_folders(name, prefix):
    sub_folders = []
    bucket = S3_RESOURCE.Bucket(name=name)
    for obj in bucket.objects.filter(Prefix=prefix):
        parts = obj.key.split("/")
        parts.pop(-1)
        folder = '/'.join(str(part) for part in parts)
        sub_folders.append(folder)
    return sub_folders


def delete_folder(name, prefix):
    objects_to_delete = S3_RESOURCE.meta.client.list_objects(Bucket=name, Prefix=prefix)
    delete_keys = {'Objects': []}
    delete_keys['Objects'] = [{'Key': k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]
    if delete_keys['Objects']:
        print("Deleting keys: {}".format(delete_keys))
        S3_RESOURCE.meta.client.delete_objects(Bucket=name, Delete=delete_keys)


def get_file(name, prefix):
    bucket = S3_RESOURCE.Bucket(name)
    response = bucket.objects.filter(
        Prefix=prefix
    )
    return response


def download_file(name, prefix, download_location):
    S3_CLIENT.download_file(name, prefix, download_location)


def upload_file(name, prefix, file):
    obj = S3_RESOURCE.Object(name, prefix)
    obj.upload_file(file)


def list_all_buckets():
    all_buckets = S3_CLIENT.list_buckets()
    return all_buckets['Buckets']
