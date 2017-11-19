"""A conduit for CI Pipelines in AWS!"""
from datetime import datetime

import boto3
import yaml

from aws_conduit import conduit_factory as factory

CONFIG_PREFIX = 'conduit.yaml'
BUCKET_PREFIX = 'conduit-config-'
IAM = boto3.client('iam')
STS = boto3.client('sts')
ROW_FORMAT = "{:<30}" * 3


def configure():
    """
    Setup necessary resources for running Conduit

    Return:
        bucket: An object handle on the Conduit configuration bucket.
    """
    account_id = STS.get_caller_identity().get('Account')
    print("Account Id: " + account_id)
    bucket_name = BUCKET_PREFIX + account_id
    bucket = factory.s3(bucket_name)
    if not bucket.exists():
        print("Creating S3: " + bucket_name)
        bucket.create()
        print("Setting initial configuration...")
        bucket.put_config(dict(created=datetime.now()), CONFIG_PREFIX)
    return bucket


def new_portfolio(name, description, tags=None):
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
    bucket = configure()
    alias = get_alias()
    if alias:
        print("Creating a new portfolio...")
        portfolio = factory.portfolio(name, alias, portfolio_description=description)
        portfolio.create(tags)
        print("Create complete...")
        config = bucket.get_config(CONFIG_PREFIX)
        if 'portfolios' not in config:
            config['portfolios'] = []
        config['portfolios'].append(portfolio)
        bucket.put_config(config, CONFIG_PREFIX)
        return portfolio
    else:
        raise ValueError('An account alias needs to be set!')


def update_portfolio(portfolio_id, name=None, description=None):
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
    bucket = configure()
    config = bucket.get_config(CONFIG_PREFIX)
    print("Updating portfolio with id: {}".format(portfolio_id))
    for portfolio in config['portfolios']:
        if portfolio.portfolio_id == portfolio_id:
            if name is not None:
                portfolio.name = name
            if description is not None:
                portfolio.description = description
            portfolio.update()
            print("Portfolio updated successfully...")
            break

    bucket.put_config(config, CONFIG_PREFIX)


def delete_portfolio(portfolio_id):
    """
    Delete a portfolio.

    Args:
        id (str): The id of the portfolio to delete.
    """
    if portfolio_id is None:
        raise ValueError("A portfolio id must be provided")
    bucket = configure()
    config = bucket.get_config(CONFIG_PREFIX)
    print("Deleting portfolio with id: {}".format(portfolio_id))
    for portfolio in config['portfolios']:
        if portfolio.portfolio_id == portfolio_id:
            for product in portfolio.products:
                print("Disassociating product with id: {}".format(product.product_id))
                product.disassociate(portfolio.portfolio_id)
            portfolio.delete()
            config['portfolios'].remove(portfolio)

    bucket.put_config(config, CONFIG_PREFIX)


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


def new_product(name, description, cfntype, portfolio_name, tags=None):
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
    bucket = configure()
    alias = get_alias()
    print("Creating a new product...")
    product = factory.product(name, alias, bucket,
                              cfntype, portfolio_name,
                              product_description=description)
    portfolio = factory.portfolio(portfolio_name, alias)
    portfolio_id = portfolio.get_id()
    config = bucket.get_config(CONFIG_PREFIX)
    support = dict() if 'support' not in config else config['support']
    product.create(support, tags)
    print("Product created...")
    product.add_to_portfolio(portfolio_id)
    print("Product assigned to portfolio: {}".format(portfolio_id))
    for portfolio in config['portfolios']:
        if portfolio.name == portfolio_name:
            portfolio.products.append(product)
    bucket.put_config(config, CONFIG_PREFIX)
    return product


def update_product(product_id, name, description, cfntype, tags=None):
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
    bucket = configure()
    config = bucket.get_config(CONFIG_PREFIX)
    print("Updating product with id: {}".format(product_id))
    for portfolio in config['portfolios']:
        for product in portfolio.products:
            if product.product_id == product_id:
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
                break

    bucket.put_config(config, CONFIG_PREFIX)


def delete_product(product_id):
    """
    Delete a product.

    Args:
        id (str): The id of the product to delete.
    """
    if product_id is None:
        raise ValueError("A product ID must be provided")
    bucket = configure()
    config = bucket.get_config(CONFIG_PREFIX)
    print("Deleting product with id: {}".format(product_id))
    for portfolio in config['portfolios']:
        for product in portfolio.products:
            if product.product_id == product_id:
                product.delete()
                portfolio.products.remove(product)
                print("Product deleted successfully...")
                break

    bucket.put_config(config, CONFIG_PREFIX)


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


def get_alias():
    """
    Get the users account alias.

    Return:
        alias: The first known account alias.
    """
    aliases = IAM.list_account_aliases()
    if aliases and aliases['AccountAliases']:
        return aliases['AccountAliases'][0]


def set_default_support_config(description=None, email=None, url=None):
    """
    Set the support configuration for your Service Catalog products.

    Args:
        description (str): Support information about the product.
        email (str): Contact email for product support.
        url (str): Contact URL for product support.
    """
    bucket = configure()
    print("Reading current configuration...")
    config = bucket.get_config(CONFIG_PREFIX)
    support = dict()
    if description:
        support['description'] = description
    if email:
        support['email'] = email
    if url:
        support['url'] = url
    config['support'] = support
    print("Writing new support configuration...")
    bucket.put_config(config, CONFIG_PREFIX)


def build():
    print("Rekeasing a new build version...")
    bucket = configure()
    spec = yaml.safe_load(open('conduitspec.yaml').read())
    config = bucket.get_config(CONFIG_PREFIX)
    portfolio = None
    product = None
    for port in config['portfolios']:
        if port.name == spec['portfolio']:
            portfolio = port
            for prod in portfolio.products:
                if prod.name == spec['product']:
                    product = prod
                    break
            break
    if not portfolio.exists():
        raise ValueError("The specified portfolio does not exist: {}".format(config['portfolio']))
    if not product.exists():
        raise ValueError("The specified product does not exist: {}".format(config['product']))

    product.release_new_build(spec['cfn']['template'], product.version)

    bucket.put_config(config, CONFIG_PREFIX)
