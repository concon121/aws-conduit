"""Helper methods for working with S3"""
import os
import tempfile

import yaml

import attr
from aws_conduit.aws import s3

LOCAL_STORE = tempfile.gettempdir()
if not os.path.exists(LOCAL_STORE):
    os.makedirs(LOCAL_STORE)


@attr.s
class ConduitS3(yaml.YAMLObject):
    """S3 helper class."""
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Bucket'
    name = attr.ib()
    region = attr.ib()

    def exists(self):
        """Test if an S3 bucket exists."""
        all_buckets = s3.list_all_buckets()
        return bool(self.name in [bucket['Name'] for bucket in all_buckets])

    def create(self):
        """
        Create an S3 bucket.

        Args:
            name(str): The name of the S3 bucket to create.
            region(str): The region to create the S3 bucket in.
        """
        s3.create_bucket(self.name, self.region)

    def delete(self):
        """Delete an S3 bucket and all of its contents."""
        s3.delete_bucket(self.name)

    def file_exists(self, prefix):
        """
        Test if a particular file exists in an S3 bucket.

        Args:
            prefix(str): The prefix of the file to test for.
            bucket_name(str): The name of the bucket to check in.
        """
        return bool(s3.get_file(self.name, prefix))

    def get_config(self, prefix):
        """
        Get conduit config from S3 and load it from yaml.

        Args:
            prefix(str): The prefix of the yaml config.
        """
        file_name = prefix.split('/')[-1]
        s3.download_file(self.name, prefix, os.path.join(LOCAL_STORE, file_name))
        config = yaml.safe_load(open(os.path.join(LOCAL_STORE, file_name)).read())
        return config

    def put_config(self, content, prefix):
        """
        Put some yaml content into an S3 bucket.

        Args:
            content(dict): An object representnig some yaml configuration.
            prefix(str): The prefix to save the configuration to.
        """
        if isinstance(content, dict):
            file_name = prefix.split('/')[-1]
            print("Uploading {} to {}...".format(file_name, self.name))
            open(os.path.join(LOCAL_STORE, file_name), "w+").write(yaml.dump(content, default_flow_style=False))
        else:
            print("Uploading {} to {}...".format(content, self.name))
            file_name = content
        s3.upload_file(self.name, prefix, os.path.join(LOCAL_STORE, file_name))

    def put_resource(self, path, prefix):
        """
        Put some yaml content into an S3 bucket.

        Args:
            path(dict): An object representnig some yaml configuration.
            prefix(str): The prefix to save the configuration to.
        """
        print("Uploading {} to {}...".format(path, self.name))
        s3.upload_file(self.name, prefix, path)

    def get_url(self):
        """Get the https url for this S3 bucket."""
        return "https://s3.{}.amazonaws.com/{}".format(self.region, self.name)
