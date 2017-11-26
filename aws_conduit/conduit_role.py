import attr
import boto3
import yaml
from aws_conduit.aws import iam


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
            role = iam.create_role(self.name, 'Conduit deploy role.')
            self.role_id = role['RoleId']
            self.role_arn = role['Arn']

    def update_policy(self, policy):
        print('Updating policy for IAM role: {}'.format(self.name))
        iam.put_role_policy(self.name, 'deployer-policy', policy)

    def _find_role(self):
        if self.role_arn is None:
            response = iam.list_roles('/conduit/')
            for role in response:
                if role['RoleName'] == self.name:
                    print('Syncing role...')
                    self.role_id = role['RoleId']
                    self.role_arn = role['Arn']
                    break
