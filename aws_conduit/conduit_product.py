import attr
import boto3
import semver
import yaml
from aws_conduit import conduit_factory as factory
from aws_conduit import helper
from aws_conduit.aws import s3, service_catalog


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
    template = attr.ib(default=None)
    template_prefix = attr.ib(default=None)
    product_id = attr.ib(default=None)
    version = attr.ib(default="0.0.0")
    provisioned = attr.ib(default=[])
    role = attr.ib(default=None)
    resources = attr.ib(default=[])

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
        if not self.template:
            self.template = "{}/{}/{}/{}/{}.{}".format(self.bucket.get_url(), self.portfolio, self.name, self.version, self.name, self.cfn_type)
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
        create_response = service_catalog.create_product(self, email, url, description, [], self.template)
        self.product_id = create_response['ProductViewDetail']['ProductViewSummary']['ProductId']

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
        service_catalog.associate(self.product_id, portfolio_id)

    def set_product_id(self):
        if self.product_id is None:
            summary = self.get_summary()
            self.product_id = summary['ProductId']

    def get_summary(self):
        response = service_catalog.search(self.name)
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
        service_catalog.update_product(self.product_id,
                                       self.name,
                                       self.owner,
                                       self.description,
                                       description,
                                       email,
                                       url)

    def disassociate(self, portfolio):
        service_catalog.disassociate(self.product_id, portfolio)

    def get_all_portfolios(self):
        self.set_product_id()
        return service_catalog.list_portfolios_for_product(self.product_id)

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
        helper.put_resource(local_template, local_template, self.bucket, self.portfolio, self.name, product_version, environment=None)
        for resource in self.resources:
            helper.put_resource(resource, resource, self.bucket, self.portfolio, self.name, product_version, environment=None)
        template_url = "{}/{}/{}/{}/{}".format(self.bucket.get_url(), self.portfolio, self.name, product_version, local_template)
        print("Creating new version to template: {}".format(template_url))
        service_catalog.new_version(self.product_id, product_version, template_url)
        self.version = product_version
        print("Released new product version: {}".format(product_version))

    def add_resources(self, product_spec):
        self.resources = []
        if 'associatedResources' in product_spec:
            for resource in product_spec['associatedResources']:
                self.resources.append(resource)
        if 'nestedStacks' in product_spec:
            for resource in product_spec['nestedStacks']:
                self.resources.append(resource)

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
        service_catalog.delete_version(self.product_id, version_id)
        prefix = "{}/{}/{}".format(self.portfolio, self.name, version_name)
        s3.delete_folder(self.bucket.name, prefix)

    def get_all_versions(self):
        return service_catalog.list_all_versions(self.product_id)

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
        is_provisioned = service_catalog.is_provisioned(name)
        if is_provisioned:
            print("Updating now...")
            service_catalog.update_provisioned(servicecatalog, self, name, params)
            print("Update success!")
        else:
            print("Provisioning now...")
            service_catalog.provision(servicecatalog, self, name, params)
            print("Provision success!")

    def terminate(self, name):
        servicecatalog = self._get_assumed_conduit_servicecatalog()
        is_provisioned = service_catalog.is_provisioned(name)
        if is_provisioned:
            print("Terminating now...")
            service_catalog.terminate_provisioned(servicecatalog, name)
        else:
            print("Artifact is not provisioned.")

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

    def create_deployer_launch_constraint(self, portfolio, role_name):
        print("Creating Launch configuration...")
        response = service_catalog.list_product_constraints(portfolio.portfolio_id, self.product_id)
        exists = False
        for item in response:
            if item['Type'] == 'LAUNCH':
                print("Launch configuration exists, nothing to do.")
                exists = True
                break
        if not exists:
            role_arn = "arn:aws:iam::{}:role/conduit/{}".format(helper.get_account_id(), role_name)
            params = dict(
                RoleArn=role_arn
            )
            service_catalog.create_constraint(portfolio.portfolio_id, self.product_id, params, self.name)
