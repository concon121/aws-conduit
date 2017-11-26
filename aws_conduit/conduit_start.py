from datetime import datetime

import attr
from aws_conduit import conduit_factory as factory
from aws_conduit.aws import iam

BUCKET_PREFIX = 'conduit-config-'
CONFIG_PREFIX = 'conduit.yaml'


@attr.s
class ConduitStart(object):

    account_id = attr.ib()

    def create_s3(self):
        bucket_name = BUCKET_PREFIX + self.account_id
        bucket = factory.s3(bucket_name)
        if not bucket.exists():
            print("Creating S3: " + bucket_name)
            bucket.create()
            print("Setting initial configuration...")
            bucket.put_config(dict(created=datetime.now()), CONFIG_PREFIX)
        return bucket

    def create_iam_role(self):
        response = iam.list_roles('/conduit/')
        if not response:
            print('Setting up IAM role...')
            iam.add_policy('conduit-provisioner-role', 'ServiceCatalogAdminFullAccess')
            iam.add_policy('conduit-provisioner-role', 'ServiceCatalogEndUserAccess')
