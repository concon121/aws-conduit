"""A conduit for CI Pipelines in AWS!"""
import json
import subprocess

import boto3
import yaml

from aws_conduit import conduit_factory as factory
from aws_conduit import helper
from aws_conduit.helper import inject_config

CONFIG_PREFIX = 'conduit.yaml'

ROW_FORMAT = "{:<30}" * 3


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
            print("Associating conduit with {}".format(portfolio.name))
            portfolio.associate_conduit(account_id)


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


def list_portfolios(token=None):
    print(ROW_FORMAT.format("Name", "Id", "Description"))
    print("----------" * 9)
    _list_all_portfolios()


def _list_all_portfolios(token=None):
    service_catalog = boto3.client('servicecatalog')
    if token is not None:
        response = service_catalog.list_portfolios(
            PageToken=token
        )
    else:
        response = service_catalog.list_portfolios()
    for portfolio in response['PortfolioDetails']:
        print(ROW_FORMAT.format(portfolio['DisplayName'], portfolio['Id'], portfolio['Description']))
    if 'NextPageToken' in response:
        _list_all_portfolios(token=response['NextPageToken'])


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
def delete_product(product_id, product_name, config=None):
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

    client = boto3.client('servicecatalog')
    client.associate_product_with_portfolio(
        ProductId=product_id,
        PortfolioId=portfolio_id
    )

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
def provision_product(product_id, product_name, name, config=None):
    if product_id is None:
        raise ValueError("A product id must be provided")
    print("Provisioning product...")
    product = helper.get_product(config, product_id=product_id)
    _provision(product, name)


def list_products():
    print(ROW_FORMAT.format("Name", "Id", "Description"))
    print("----------" * 9)
    _list_all_products()


def _list_all_products(token=None):
    service_catalog = boto3.client('servicecatalog')
    if token is not None:
        response = service_catalog.search_products_as_admin(
            PageToken=token
        )
    else:
        response = service_catalog.search_products_as_admin()
    for product in response['ProductViewDetails']:
        summary = product['ProductViewSummary']
        print(ROW_FORMAT.format(summary['Name'], summary['ProductId'], summary['ShortDescription']))
    if 'NextPageToken' in response:
        _list_all_portfolios(token=response['NextPageToken'])


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


@inject_config
def build(action, config=None):
    print("Releasing a new build version...")
    spec = yaml.safe_load(open('conduitspec.yaml').read())
    for product_spec in spec['products']:
        product = helper.find_build_product(product_spec['name'], spec, config)
        if 'build' in product_spec:
            for step in product_spec['build']:
                subprocess.call(step, shell=True)
        print(product_spec)
        update_iam_role(product_spec, product)
        product.create_deployer_launch_constraint(helper.get_portfolio(config, name=spec['portfolio']))
        product.release(action, product_spec['artifact'], product.version)
        if 'associatedResources' in product_spec:
            for resource in product_spec['associatedResources']:
                product.put_resource(resource)
        if action != 'build':
            product.tidy_versions()


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
        product = helper.find_build_product(product_name, spec, config)
        update_iam_role(product_spec, product)
        _provision(product, name)
        if not hasattr(product, 'provisioned'):
            product.provisioned = []
        product.provisioned.append(name)
    else:
        raise ValueError("No products defined in conduitspec.yaml")


def _provision(product, name):
    version_id = product.get_version_id()
    client = boto3.client('servicecatalog')
    launch_paths = client.list_launch_paths(
        ProductId=product.product_id,
    )
    print("Getting launch path...")
    if launch_paths['LaunchPathSummaries']:
        launch_path = launch_paths['LaunchPathSummaries'][0]['Id']
        response = client.describe_provisioning_parameters(
            ProductId=product.product_id,
            ProvisioningArtifactId=version_id,
            PathId=launch_path
        )
        print("Getting input parameters...")
        params = []
        # conduit-config-977855701381/andover-ci/product-stack/0.0.0+build.6
        params.append(dict(
            Key="ConduitStackKey",
            Value="{}/{}/{}/{}".format(product.bucket.name,
                                       product.portfolio,
                                       product.name,
                                       product.version)
        ))
        for param in response['ProvisioningArtifactParameters']:
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
    #product = helper.find_provisioned_build_product(provisioned_product_name, spec, config)
    product.terminate(provisioned_product_name)
    product.provisioned.remove(provisioned_product_name)


def update_iam_role(spec, product):
    print(product)
    try:
        if 'roleName' in spec:
            product.create_role(spec['roleName'])
        else:
            raise ValueError('A roleName must be specified for your product.')
    except:
        print('Role probably already exists...')

    if 'deployProfile' in spec:
        print('Updating IAM Role...')
        statements = []
        policy = dict(
            Version="2012-10-17",
            Statement=statements
        )
        for entry in spec['deployProfile']:
            statement = dict(
                Effect="Allow",
                Action=entry['actions'],
                Resource=entry['resources']
            )
            statements.append(statement)

        product.role.update_policy(policy)
    else:
        raise ValueError('No deploy profile.  Will not continute...')
