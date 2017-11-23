import json

import boto3
import yaml

import attr


@attr.s
class ConduitRole(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Role'

    name = attr.ib()
    role_id = attr.ib(default=None)
    role_arn = attr.ib(default=None)

    iam = boto3.client('iam')

    def create(self):
        self._find_role()
        if self.role_arn is None:
            print('Creating role: {}'.format(self.name))
            role_policy = {
                'Statement': [
                    {
                        'Principal': {
                            'Service': 'servicecatalog.amazonaws.com'
                        },
                        'Effect': 'Allow',
                        'Action': ['sts:AssumeRole']
                    },
                ]
            }
            response = self.iam.create_role(
                Path='/conduit/',
                RoleName=self.name,
                AssumeRolePolicyDocument=json.dumps(role_policy),
                Description='Conduit deploy role.'
            )
            self.role_id = response['Role']['RoleId']
            self.role_arn = response['Role']['Arn']

    def update_policy(self, policy):
        print('Updating policy for IAM role: {}'.format(self.name))
        self.iam.put_role_policy(
            RoleName=self.name,
            PolicyName='deployer-policy',
            PolicyDocument=json.dumps(policy)
        )

    def _find_role(self, token=None):
        if self.role_arn is None:
            if token is None:
                response = self.iam.list_roles(
                    PathPrefix='/conduit/'
                )
            else:
                response = self.iam.list_roles(
                    PathPrefix='/conduit/',
                    Marker=token
                )
            for role in response['Roles']:
                if role['RoleName'] == self.name:
                    print('Syncing role...')
                    self.role_id = role['RoleId']
                    self.role_arn = role['Arn']
                    break
            if 'Marker' in response:
                self._find_role(token=response['Marker'])
