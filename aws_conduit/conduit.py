"""A conduit for CI Pipelines in AWS!"""
import json
import os
import subprocess

import semver
import yaml
from aws_conduit import conduit_factory as factory
from aws_conduit import conduit_s3, helper
from aws_conduit.aws import iam, s3, service_catalog
from aws_conduit.helper import inject_config

CONFIG_PREFIX = 'conduit.yaml'


def configure():
    """
    Setup necessary resources for running Conduit

    Return:
        bucket: An object handle on the Conduit configuration bucket.
    """
    start = factory.start()
    bucket = start.create_s3()
    start.create_iam_role()
    return bucket


@inject_config
def sync(config=None):
    account_id = helper.get_account_id()
    print("Ensuring Conduit is up to date...")
    if 'portfolios' in config:
        for portfolio in config['portfolios']:
            if portfolio.exists():
                print("Associating conduit with {}".format(portfolio.name))
                portfolio.associate_conduit(account_id)
            else:
                print("Portfolio no longer exists!")
                config['portfolios'].remove(portfolio)


@inject_config
def new_portfolio(name, description, tags=None, config=None):
    """
    Create a new portfolio.

    Args:
        name (str): The name of the portfolio to create.
        description (str): A description of the portfolio to create.
        tags (list): An optional list of tags to apply to all products in the portfolio.

    Return:
        portfolio: An object handle on the new portfolio.
    """
    if name is None or description is None:
        raise ValueError("name and description must have values")
    if tags is None:
        tags = []
    alias = helper.get_alias()
    if alias:
        print("Creating a new portfolio...")
        portfolio = factory.portfolio(name, portfolio_description=description)
        portfolio.create(tags)
        print("Create complete...")
        if 'portfolios' not in config:
            config['portfolios'] = []
        config['portfolios'].append(portfolio)
        return portfolio
    else:
        raise ValueError('An account alias needs to be set!')


@inject_config
def update_portfolio(portfolio_id, name=None, description=None, config=None):
    """
    Update a portfolio.

    Args:
        name (str): The name of the portfolio to create.
        description (str): A description of the portfolio to create.

    Return:-
        portfolio: An object handle on the portfolio.
    """
    if portfolio_id is None:
        raise ValueError("A portfolio ID must be provided")
    print("Updating portfolio with id: {}".format(portfolio_id))
    portfolio = helper.get_portfolio(config, portfolio_id=portfolio_id)
    if name is not None:
        portfolio.name = name
    if description is not None:
        portfolio.description = description
    portfolio.update()
    print("Portfolio updated successfully...")


@inject_config
def delete_portfolio(portfolio_id, config=None):
    """
    Delete a portfolio.

    Args:
        id (str): The id of the portfolio to delete.
    """
    if portfolio_id is None:
        raise ValueError("A portfolio id must be provided")
    print("Deleting portfolio with id: {}".format(portfolio_id))
    portfolio = helper.get_portfolio(config, portfolio_id=portfolio_id)
    for product in portfolio.products:
        print("Disassociating product with id: {}".format(product.product_id))
        product.disassociate(portfolio.portfolio_id)
    portfolio.delete()
    config['portfolios'].remove(portfolio)


def list_portfolios():
    print(service_catalog.ROW_FORMAT.format("Name", "Id", "Description"))
    print("----------" * 9)
    service_catalog.list_all_portfolios()


@inject_config
def new_product(name, description, cfntype, portfolio_name, tags=None, config=None):
    """
    Create a new product.

    Args:
        name (str): The name of the product to create.
        description (str): A brief description of the product.
        cfntype (str): One of [json, yaml, yml]
        portfolio_name (str): The name of the portfolio to add the product to.

    Return:
        product: An object handle on the new product.
    """
    if name is None or description is None or cfntype is None or portfolio_name is None:
        raise ValueError("name, description, cfntype and portfolio_name must have values")
    if tags is None:
        tags = []
    print("Creating a new product...")
    product = factory.product(name, portfolio_name, product_description=description)
    portfolio = factory.portfolio(portfolio_name)
    portfolio_id = portfolio.get_id()
    support = dict() if 'support' not in config else config['support']
    product.create(support, tags)
    print("Product created...")
    product.add_to_portfolio(portfolio_id)
    print("Product assigned to portfolio: {}".format(portfolio_id))
    portfolio = helper.get_portfolio(config, name=portfolio_name)
    portfolio.products.append(product)
    return product


@inject_config
def update_product(product_id, name, description, cfntype, tags=None, config=None):
    """
    Update a portfolio.

    Args:
        name (str): The name of the portfolio to create.
        description (str): A description of the portfolio to create.

    Return:-
        portfolio: An object handle on the portfolio.
    """
    if product_id is None:
        raise ValueError("A product ID must be provided")
    print("Updating product with id: {}".format(product_id))
    product = helper.get_product(config, product_id=product_id)
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if cfntype is not None:
        product.cfntype = cfntype
    if tags is not None:
        product.tags = tags
    support = dict()
    if 'support' in config:
        support = config['support']
    product.update(support)
    print("Product updated successfully...")


@inject_config
def delete_product(product_id, config=None):
    """
    Delete a product.

    Args:
        id (str): The id of the product to delete.
    """
    if product_id is None:
        raise ValueError("A product ID must be provided")
    print("Deleting product with id: {}".format(product_id))
    for portfolio in config['portfolios']:
        for product in portfolio.products:
            if product.product_id == product_id:
                product.delete()
                portfolio.products.remove(product)
                print("Product deleted successfully...")
                break


@inject_config
def associate_product_with_portfolio(product_id, portfolio_id, config=None):
    if portfolio_id is None:
        raise ValueError("A portfolio id must be provided")
    if product_id is None:
        raise ValueError("A product id must be provided")

    portfolio = helper.get_portfolio(config, portfolio_id=portfolio_id)
    if portfolio is None:
        raise ValueError("Provided portfolio does not exist in Conduit config!")

    bucket = configure()
    print("Associating product with portfolio...")
    service_catalog.associate(product_id, portfolio_id)
    print("Association successful...")
    print("Finding product by id...")
    product = factory.product_by_id(product_id, bucket)
    print("Reflecting changes in Conduit config...")
    portfolio.products.append(product)
    product.portfolio = portfolio.name


@inject_config
def terminate_provisioned_product(product_id, stack_name, config=None):
    if product_id is None:
        raise ValueError("A product id must be provided")
    print("Terminating product...")
    product = helper.get_product(config, product_id=product_id)
    product.terminate(stack_name)


@inject_config
def provision_product(product_id, name, config=None):
    if product_id is None:
        raise ValueError("A product id must be provided")
    print("Provisioning product...")
    product = helper.get_product(config, product_id=product_id)
    _provision(product, name)


def list_products():
    print(service_catalog.ROW_FORMAT.format("Name", "Id", "Description"))
    print("----------" * 9)
    service_catalog.list_all_products()


@inject_config
def set_default_support_config(description=None, email=None, url=None, config=None):
    """
    Set the support configuration for your Service Catalog products.

    Args:
        description (str): Support information about the product.
        email (str): Contact email for product support.
        url (str): Contact URL for product support.
    """
    print("Reading current configuration...")
    support = dict()
    if description:
        support['description'] = description
    if email:
        support['email'] = email
    if url:
        support['url'] = url
    config['support'] = support
    print("Writing new support configuration...")


def build(action, product):
    print("Releasing a new build version...")
    spec = yaml.safe_load(open('conduitspec.yaml').read())
    for product_spec in spec['inventory']:
        if (product is not None and product_spec['product'] == product) or product is None:
            # Perform Build Steps
            if 'serviceCatalog' in product_spec and product_spec['serviceCatalog']:
                if 'build' in product_spec:
                    for step in product_spec['build']:
                        subprocess.call(step, shell=True)
                _service_catalog_build(action, product_spec)
            else:
                print(product_spec)
                _s3_build(action, product_spec)


@inject_config
def _service_catalog_build(action, product_spec, config=None):
    result = helper.find_build_product(product_spec, config)
    if result['product'] is None:
        raise ValueError('Product was not found in config!')
    product = result['product']
    print(product_spec)
    update_iam_role(product_spec)
    product.add_resources(product_spec)
    if 'roleName' in product_spec:
        product.create_deployer_launch_constraint(helper.get_portfolio(config, name=product_spec['portfolio']), product_spec['roleName'])
    product.release(action, product_spec['artifact'], product.version)
    if action != 'build':
        product.tidy_versions()


@inject_config
def _s3_build(action, product_spec, config=None):
    print(product_spec)
    result = helper.find_s3_build_product(product_spec, config)
    next_version = helper.next_version(action, result['product']['currentVersion'])
    print("The next version is: {}".format(next_version))
    result['product']['currentVersion'] = next_version
    if 'nextVersion' in result['product']:
        del result['product']['nextVersion']
    if 'policy' in result['product']:
        del result['product']['policy']
    if 'deployProfile' in result['product']:
        del result['product']['deployProfile']
    start = factory.start()
    bucket = start.create_s3()
    sls_package = None

    if 'build' in product_spec:
        for step in product_spec['build']:
            subprocess.call(step, shell=True, env=dict(os.environ, VERSION=next_version))

    if 'sls' in product_spec and product_spec['sls'] is True:
        sls_state = json.load(open('.serverless/serverless-state.json'))
        sls_package = sls_state['package']
        sls_package['bucket'] = sls_state['service']['provider']['deploymentBucketObject']['name']
        result['product']['template'] = helper.put_sls_resource(
            product_spec['artifact'], bucket, product_spec['portfolio'], product_spec['product'], next_version, sls_package)
    else:
        result['product']['template'] = helper.put_resource(
            product_spec['artifact'], product_spec['artifact'], bucket, product_spec['portfolio'], product_spec['product'], next_version)
    if 'associatedResources' in product_spec:
        _put_resources(product_spec['associatedResources'], product_spec, bucket, next_version, sls_package)
    if 'nestedStacks' in product_spec:
        _put_resources(product_spec['nestedStacks'], product_spec, bucket, next_version, sls_package)
    result['product'].update(product_spec)


def _tidy_versions(portfolio, product, version, bucket):
    versions = s3.get_sub_folders(bucket.name, "{}/{}/{}".format(portfolio, product, 'core'))
    for item in versions:
        this_version = item.split("/")[-1]
        if ('+build' in this_version and
                semver.compare(this_version, version) == -1):
            prefix = "{}/{}/{}/{}".format(portfolio, product, 'core', this_version)
            print("Tidying version: {}".format(prefix))
            s3.delete_folder(bucket.name, prefix)


def _put_resources(resources, product_spec, bucket, next_version, sls_package):
    for resource in resources:
        if 'sls' in product_spec and product_spec['sls'] is True:
            helper.put_sls_resource(resource, bucket, product_spec['portfolio'], product_spec['product'], next_version, sls_package)
        else:
            if isinstance(resource, str):
                source_path = resource
                destination_path = resource
            else:
                source_path = resource['source']
                destination_path = resource['destination']
            helper.put_resource(source_path, destination_path, bucket, product_spec['portfolio'], product_spec['product'], next_version)


@inject_config
def package_portfolio(portfolio_name, environment, config=None):
    package = helper.get_all_portfolio_artifacts(portfolio_name, config)
    print(json.dumps(package))

    start = factory.start()
    bucket = start.create_s3()

    file_name = '{}.json'.format(portfolio_name)
    file_path = os.path.join(conduit_s3.LOCAL_STORE, file_name)
    zip_name = '{}-{}.zip'.format(portfolio_name, environment)
    zip_path = os.path.join(conduit_s3.LOCAL_STORE, zip_name)
    open(file_path, "w+").write(json.dumps(package))
    subprocess.call('cd {} && zip -r {} {}'.format(conduit_s3.LOCAL_STORE, zip_name, file_name), shell=True)
    bucket.put_resource(zip_path, '{}/{}-{}.zip'.format(portfolio_name, portfolio_name, environment))


@inject_config
def package_product(portfolio_name, product_name, environment, config=None):
    package = []
    results = helper.get_all_portfolio_artifacts(portfolio_name, config)
    for result in results:
        if 'name' in result and result['name'] == product_name:
            package.append(result)
        elif 'product' in result and result['product'] == product_name:
            package.append(result)
    print(json.dumps(package))

    start = factory.start()
    bucket = start.create_s3()

    file_name = '{}-{}.json'.format(portfolio_name, product_name)
    file_path = os.path.join(conduit_s3.LOCAL_STORE, file_name)
    zip_name = '{}-{}-{}.zip'.format(portfolio_name, product_name, environment)
    zip_path = os.path.join(conduit_s3.LOCAL_STORE, zip_name)
    open(file_path, "w+").write(json.dumps(package))
    subprocess.call('cd {} && zip -r {} {}'.format(conduit_s3.LOCAL_STORE, zip_name, file_name), shell=True)
    bucket.put_resource(zip_path, '{}/{}-{}-{}.zip'.format(portfolio_name, portfolio_name, product_name, environment))


@inject_config
def provision_product_build(product_name, name, config=None):
    if name is None:
        raise ValueError("A stage must be provided")
    spec = yaml.safe_load(open('conduitspec.yaml').read())
    if 'products' in spec:
        product_spec = None
        for product in spec['products']:
            if product['name'] == product_name:
                product_spec = product
        if product_spec is None:
            raise ValueError("The requested product was not defined in conduitspec.yaml")
        print("Provisioning product...")
        product = helper.find_build_product(spec, config)
        update_iam_role(product_spec)
        _provision(product, name)
        if not hasattr(product, 'provisioned'):
            product.provisioned = []
        product.provisioned.append(name)
    else:
        raise ValueError("No products defined in conduitspec.yaml")


def _provision(product, name):
    version_id = product.get_version_id()
    launch_paths = service_catalog.get_all_launch_paths(product.product_id)
    print("Getting launch path...")
    if launch_paths:
        launch_path = launch_paths[0]['Id']
        print("Getting input parameters...")
        provisioning_params = service_catalog.get_provisioning_parameters(product.product_id,
                                                                          version_id,
                                                                          launch_path)
        params = []
        for param in provisioning_params:
            if param['ParameterKey'] != "ConduitStackKey":
                if 'DefaultValue' in param:
                    input_value = input('{} (Default: {}): '.format(param['ParameterKey'],
                                                                    param['DefaultValue']))
                else:
                    input_value = input('{}: '.format(param['ParameterKey']))
                if input_value is None or input_value == '':
                    input_value = param['DefaultValue']
                param = dict(
                    Key=param['ParameterKey'],
                    Value=input_value
                )
                params.append(param)
        print(params)
        product.provision(params, name)


@inject_config
def terminate_product(provisioned_product_name, config=None):
    if provisioned_product_name is None:
        raise ValueError("A product name must be provided")
    spec = yaml.safe_load(open('conduitspec.yaml').read())
    print("Terminating product...")
    product = None
    for port in config['portfolios']:
        if port.name == spec['portfolio']:
            portfolio = port
            for prod in portfolio.products:
                product = prod
                break
    product.terminate(provisioned_product_name)
    product.provisioned.remove(provisioned_product_name)


def update_iam_role(spec):
    if 'roleName' in spec:
        try:
            iam.create_role(spec['roleName'], 'Deployer role for {}'.format(spec['name']))
        except:
            print('Role probably already exists...')
        try:
            iam.add_policy(spec['roleName'], 'ServiceCatalogEndUserFullAccess')
        except:
            print('Policy probably already added')
        try:
            iam.add_policy(spec['roleName'], 'AdministratorAccess')
        except:
            print('Policy probably already added!')
