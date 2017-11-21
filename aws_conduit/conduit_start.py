import json
from datetime import datetime

import attr
import boto3
from aws_conduit import conduit_factory as factory

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
        iam = boto3.client('iam')
        response = iam.list_roles(
            PathPrefix='/conduit/'
        )
        if not response['Roles']:
            print('Setting up IAM role...')
            basic_role_policy = {
                'Statement': [
                    {
                        'Principal': {
                            'AWS': self.account_id
                        },
                        'Effect': 'Allow',
                        'Action': ['sts:AssumeRole']
                    },
                ]
            }
            iam.create_role(
                Path='/conduit/',
                RoleName='conduit-provisioner-role',
                AssumeRolePolicyDocument=json.dumps(basic_role_policy),
                Description='Deploy role for the Conduit automation tool'
            )
            iam.attach_role_policy(
                RoleName='conduit-provisioner-role',
                PolicyArn='arn:aws:iam::aws:policy/ServiceCatalogAdminFullAccess'
            )
            iam.attach_role_policy(
                RoleName='conduit-provisioner-role',
                PolicyArn='arn:aws:iam::aws:policy/ServiceCatalogEndUserAccess'
            )