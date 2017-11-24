import fileinput
import json
from datetime import datetime

import boto3
import yaml

import attr
import semver
from aws_conduit import conduit_factory as factory

RESOURCES_KEY = "__resources__"


@attr.s
class ConduitProduct(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Product'
    name = attr.ib()
    owner = attr.ib()
    bucket = attr.ib()
    cfn_type = attr.ib()
    portfolio = attr.ib()
    description = attr.ib(default='No description set')
    template_location = attr.ib(default=None)
    template_prefix = attr.ib(default=None)
    product_id = attr.ib(default=None)
    version = attr.ib(default="0.0.0")
    provisioned = attr.ib(default=[])
    role = attr.ib(default=None)
    service_catalog = boto3.client('servicecatalog')

    def _add_initial_template(self):
        template = dict(
            AWSTemplateFormatVersion="2010-09-09",
            Resources=dict(
                FalseS3=dict(
                    Type="AWS::S3::Bucket",
                    Properties=dict(
                        AccessControl="private"
                    )
                )
            ))
        self.bucket.put_config(template, self.template_prefix)

    def create(self, support, tags):
        """
        Create a new product.
        """
        if not self.template_location:
            self.template_location = "{}/{}/{}/{}/{}.{}".format(self.bucket.get_url(), self.portfolio, self.name, self.version, self.name, self.cfn_type)
            self.template_prefix = "{}/{}/{}/{}.{}".format(self.portfolio, self.name, self.version, self.name, self.cfn_type)
        self._add_initial_template()
        description = 'NotSet'
        email = 'noone@home.com'
        url = 'http://notset.com'
        if 'description' in support:
            description = support['description']
        if 'email' in support:
            email = support['email']
        if 'url' in support:
            url = support['url']
        create_response = self.service_catalog.create_product(
            Name=self.name,
            Owner=self.owner,
            Description=self.description,
            Distributor=self.owner,
            SupportDescription=description,
            SupportEmail=email,
            SupportUrl=url,
            ProductType='CLOUD_FORMATION_TEMPLATE',
            Tags=tags,
            ProvisioningArtifactParameters={
                'Name': self.version,
                'Description': 'Initial product creation.',
                'Info': {
                    'LoadTemplateFromURL': self.template_location
                },
                'Type': 'CLOUD_FORMATION_TEMPLATE'
            },
        )
        self.product_id = create_response['ProductViewDetail']['ProductViewSummary']['ProductId']
        # self.create_role()

    def create_role(self, name):
        print(self.role)
        if self.role is not None:
            if self.role.name != name:
                self.role = factory.role(name)
                self.role.create()
        else:
            self.role = factory.role(name)
            self.role.create()

    def add_to_portfolio(self, portfolio_id):
        # if not self.product_id:
        self.set_product_id()
        self.service_catalog.associate_product_with_portfolio(
            ProductId=self.product_id,
            PortfolioId=portfolio_id
        )

    def set_product_id(self):
        if self.product_id is None:
            summary = self.get_summary()
            self.product_id = summary['ProductId']

    def get_summary(self):
        response = self.service_catalog.search_products_as_admin(
            Filters={
                'FullTextSearch': [
                    self.name,
                ]
            }
        )
        if 'ProductViewDetails' in response:
            for item in response['ProductViewDetails']:
                if item['ProductViewSummary']:
                    summary = item['ProductViewSummary']
                    if (summary['Name'] == self.name and
                            summary['Owner'] == self.owner):
                        return summary
        return None

    def exists(self):
        summary = self.get_summary()
        return bool(summary is not None)

    def delete(self):
        self.set_product_id()
        portfolios = self.get_all_portfolios()
        for portfolio in portfolios:
            self.disassociate(portfolio)
        self.service_catalog.delete_product(
            Id=self.product_id
        )

    def update(self, support):
        """
        Updates this Product instance.
        """
        description = 'NotSet'
        email = 'noone@home.com'
        url = 'http://notset.com'
        if 'description' in support:
            description = support['description']
        if 'email' in support:
            email = support['email']
        if 'url' in support:
            url = support['url']
        self.service_catalog.update_product(
            Id=self.product_id,
            Name=self.name,
            Owner=self.owner,
            Description=self.description,
            Distributor=self.owner,
            SupportDescription=description,
            SupportEmail=email,
            SupportUrl=url,
        )

    def disassociate(self, portfolio):
        self.service_catalog.disassociate_product_from_portfolio(
            ProductId=self.product_id,
            PortfolioId=portfolio
        )

    def get_all_portfolios(self, token=None):
        self.set_product_id()
        if token:
            response = self.service_catalog.list_portfolios_for_product(
                ProductId=self.product_id,
                PageToken=token,
            )
        else:
            response = self.service_catalog.list_portfolios_for_product(
                ProductId=self.product_id
            )
        portfolios = [item['Id'] for item in response['PortfolioDetails']]
        if 'NextPageToken' in response:
            portfolios = portfolios + self.get_all_portfolios(token=response['NextPageToken'])
        return portfolios

    def release(self, release_type, local_template, current_version):
        product_version = current_version
        if release_type == 'build':
            product_version = semver.bump_build(current_version)
        if release_type == 'major':
            product_version = semver.bump_major(current_version)
        if release_type == 'minor':
            product_version = semver.bump_minor(current_version)
        if release_type == 'patch':
            product_version = semver.bump_patch(current_version)

        self.release_new_build(local_template, product_version)

    def release_new_build(self, local_template, product_version):
        self.replace_resources(local_template, version=product_version)
        self.bucket.put_config(local_template, "{}/{}/{}/{}.{}".format(self.portfolio, self.name, product_version, self.name, self.cfn_type))
        self.revert_resources(local_template, version=product_version)
        template_url = "{}/{}/{}/{}/{}.{}".format(self.bucket.get_url(), self.portfolio, self.name, product_version, self.name, self.cfn_type)
        print("Creating new version to template: {}".format(template_url))
        self.service_catalog.create_provisioning_artifact(
            ProductId=self.product_id,
            Parameters={
                'Name': product_version,
                'Description': 'Incremental build; Not production ready!',
                'Info': {
                    'LoadTemplateFromURL': template_url
                },
                'Type': 'CLOUD_FORMATION_TEMPLATE'
            },
            IdempotencyToken='string'
        )
        self.version = product_version
        print("Released new product version: {}".format(product_version))

    def put_resource(self, path, version=None):
        if version is None:
            key = "{}/{}/{}/{}".format(self.portfolio, self.name, self.version, path)
        else:
            key = "{}/{}/{}/{}".format(self.portfolio, self.name, version, path)
        print("Adding resource to release: {}".format(path))
        self.replace_resources(path)
        self.bucket.put_config(path, key)
        self.replace_resources(path)

    def replace_resources(self, path, version=None):
        if path.endswith('yaml') or path.endswith('yml') or path.endswith('json'):
            if version is None:
                directory = "{}/{}/{}/{}".format(self.bucket.name, self.portfolio, self.name, self.version)
            else:
                directory = "{}/{}/{}/{}".format(self.bucket.name, self.portfolio, self.name, version)

            f = open(path, 'r')
            filedata = f.read()
            f.close()

            newdata = filedata.replace(RESOURCES_KEY, directory)

            f = open(path, 'w')
            f.write(newdata)
            f.close()

    def revert_resources(self, path, version=None):
        if path.endswith('yaml') or path.endswith('yml') or path.endswith('json'):
            if version is None:
                directory = "{}/{}/{}/{}".format(self.bucket.name, self.portfolio, self.name, self.version)
            else:
                directory = "{}/{}/{}/{}".format(self.bucket.name, self.portfolio, self.name, version)
            f = open(path, 'r')
            filedata = f.read()
            f.close()

            newdata = filedata.replace(directory, RESOURCES_KEY)

            f = open(path, 'w')
            f.write(newdata)
            f.close()

    def tidy_versions(self):
        versions = self.get_all_versions()
        version = self.version
        for item in versions:
            if ('build' in item['Name'] and
                    semver.compare(item['Name'], version) == -1):
                self.delete_version(item['Name'], item['Id'])
        print("Current product version is: {}".format(version))
        return version

    def delete_version(self, version_name, version_id):
        print("Deleting version: {}".format(version_name))
        self.service_catalog.delete_provisioning_artifact(
            ProductId=self.product_id,
            ProvisioningArtifactId=version_id
        )
        key = "{}/{}/{}".format(self.portfolio, self.name, version_name)

        s3 = self.bucket.s3_resource
        objects_to_delete = s3.meta.client.list_objects(Bucket=self.bucket.name, Prefix=key)

        delete_keys = {'Objects': []}
        delete_keys['Objects'] = [{'Key': k} for k in [obj['Key'] for obj in objects_to_delete.get('Contents', [])]]

        if delete_keys['Objects']:
            print("Deleting keys: {}".format(delete_keys))
            s3.meta.client.delete_objects(Bucket=self.bucket.name, Delete=delete_keys)

    def get_all_versions(self):
        response = self.service_catalog.list_provisioning_artifacts(
            ProductId=self.product_id
        )
        return response['ProvisioningArtifactDetails']

    def get_last_version(self):
        versions = self.get_all_versions()
        version = self.version
        for item in versions:
            if semver.compare(item['Name'], version) == -1:
                version = item['Name']
                break
        print("Current product version is: {}".format(version))
        return version

    def get_version_id(self):
        versions = self.get_all_versions()
        for item in versions:
            if item['Name'] == self.version:
                return item['Id']

    def provision(self, params, name):
        servicecatalog = self._get_assumed_conduit_servicecatalog()
        is_provisioned = self.determine_if_provisioned(servicecatalog, name)
        if is_provisioned:
            print("Updating now...")
            response = servicecatalog.update_provisioned_product(
                ProvisionedProductName=name,
                ProductId=self.product_id,
                ProvisioningArtifactId=self.get_version_id(),
                ProvisioningParameters=params
            )
            print("Update success!")
        else:
            print("Provisioning now...")
            response = servicecatalog.provision_product(
                ProductId=self.product_id,
                ProvisioningArtifactId=self.get_version_id(),
                ProvisionedProductName=name,
                ProvisioningParameters=params
            )
            print("Provision success!")

    def terminate(self, name):
        servicecatalog = self._get_assumed_conduit_servicecatalog()
        is_provisioned = self.determine_if_provisioned(servicecatalog, name)
        if is_provisioned:
            print("Terminating now...")
            response = servicecatalog.terminate_provisioned_product(
                ProvisionedProductName=name,
                IgnoreErrors=False
            )
        else:
            print("Artifact is not provisioned.")

    def determine_if_provisioned(self, servicecatalog, name, token=None):
        if token:
            response = servicecatalog.scan_provisioned_products(
                PageToken='string'
            )
        else:
            response = self.service_catalog.scan_provisioned_products(
                AccessLevelFilter={
                    'Key': 'Account',
                    'Value': 'self'
                }
            )
        for product in response['ProvisionedProducts']:
            print(product)
            if product['Name'] == name:
                return True
        if 'NextPageToken' in response:
            return self.determine_if_provisioned(servicecatalog, name, token=response['NextPageToken'])
        else:
            return False

    def _get_assumed_conduit_servicecatalog(self):
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity().get('Account')
        print("Assumiing consuit IAM role...")
        creds = sts.assume_role(
            RoleArn='arn:aws:iam::{}:role/conduit/conduit-provisioner-role'.format(account_id),
            RoleSessionName='conduit-{}'.format(hash('conduit'))
        )
        servicecatalog = boto3.client(
            'servicecatalog',
            aws_access_key_id=creds['Credentials']['AccessKeyId'],
            aws_secret_access_key=creds['Credentials']['SecretAccessKey'],
            aws_session_token=creds['Credentials']['SessionToken'],
        )
        return servicecatalog

    def create_deployer_launch_constraint(self, portfolio):
        print("Creating Launch configuration...")
        response = self.service_catalog.list_constraints_for_portfolio(
            PortfolioId=portfolio.portfolio_id,
            ProductId=self.product_id
        )
        exists = False
        for item in response['ConstraintDetails']:
            if item['Type'] == 'LAUNCH':
                print("Launch configuration exists, nothing to do.")
                exists = True
                break
        if not exists:
            params = dict(
                RoleArn=self.role.role_arn
            )
            response = self.service_catalog.create_constraint(
                PortfolioId=portfolio.portfolio_id,
                ProductId=self.product_id,
                Parameters=json.dumps(params),
                Type='LAUNCH',
                Description='Launch configuration for {}'.format(self.name)
            )
