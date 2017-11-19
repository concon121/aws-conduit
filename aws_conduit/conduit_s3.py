"""Helper methods for working with S3"""
import attr
import boto3
import yaml

from aws_conduit.conduit_portfolio import ConduitPortfolio
from aws_conduit.conduit_product import ConduitProduct


@attr.s
class ConduitS3(yaml.YAMLObject):
    """S3 helper class."""
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Bucket'
    name = attr.ib()
    region = attr.ib()
    s3_resource = boto3.resource('s3')
    s3_client = boto3.client('s3')

    def exists(self):
        """Test if an S3 bucket exists."""
        all_buckets = self.s3_client.list_buckets()
        return bool(self.name in [bucket['Name'] for bucket in all_buckets['Buckets']])

    def create(self):
        """
        Create an S3 bucket.

        Args:
            name(str): The name of the S3 bucket to create.
            region(str): The region to create the S3 bucket in.
        """
        bucket = self.s3_resource.Bucket(self.name)
        bucket.create(
            ACL='private',
            CreateBucketConfiguration={
                'LocationConstraint': self.region
            }
        )
        bucket.Versioning().enable()

    def delete(self):
        """Delete an S3 bucket and all of its contents."""
        bucket = self.s3_resource.Bucket(self.name)
        bucket.objects.all().delete()
        bucket.delete()

    def file_exists(self, prefix):
        """
        Test if a particular file exists in an S3 bucket.

        Args:
            prefix(str): The prefix of the file to test for.
            bucket_name(str): The name of the bucket to check in.
        """
        bucket = self.s3_resource.Bucket(self.name)
        response = bucket.objects.filter(
            Prefix=prefix
        )
        return bool(response)

    def get_config(self, prefix):
        """
        Get conduit config from S3 and load it from yaml.

        Args:
            prefix(str): The prefix of the yaml config.
        """
        file_name = prefix.split('/')[-1]
        self.s3_client.download_file(self.name, prefix, file_name)
        config = yaml.safe_load(open(file_name).read())
        return config

    def put_config(self, content, prefix):
        """
        Put some yaml content into an S3 bucket.

        Args:
            content(dict): An object representnig some yaml configuration.
            prefix(str): The prefix to save the configuration to.
        """
        obj = self.s3_resource.Object(self.name, prefix)
        if isinstance(content, dict):
            file_name = prefix.split('/')[-1]
            print("Uploading {} to {}...".format(file_name, self.name))
            open(file_name, "w+").write(yaml.dump(content, default_flow_style=False))
            obj.upload_file(file_name)
        else:
            print("Uploading {} to {}...".format(content, self.name))
            obj.upload_file(content)
        return obj.version_id

    def get_url(self):
        """Get the https url for this S3 bucket."""
        return "https://s3.{}.amazonaws.com/{}".format(self.region, self.name)
