"""A conduit for CI Pipelines in AWS!"""
from datetime import datetime

import boto3

from aws_conduit import conduit_factory as factory

CONFIG_PREFIX = 'conduit.yaml'
BUCKET_PREFIX = 'conduit-config-'
IAM = boto3.client('iam')
STS = boto3.client('sts')


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
        portfolio = factory.portfolio(name, alias, portfolio_description=description)
        portfolio.create(tags)
        config = bucket.get_config(CONFIG_PREFIX)
        if 'portfolios' not in config:
            config['portfolios'] = []
        config['portfolios'].append(portfolio)
        bucket.put_config(config, CONFIG_PREFIX)
        return portfolio
    else:
        raise ValueError('An account alias needs to be set!')


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
    product = factory.product(name, alias, bucket,
                              cfntype, portfolio_name,
                              product_description=description)
    portfolio = factory.portfolio(portfolio_name, alias)
    portfolio_id = portfolio.get_id()
    config = bucket.get_config(CONFIG_PREFIX)
    support = dict() if 'support' not in config else config['support']
    product.create(support, tags)
    product.add_to_portfolio(portfolio_id)
    for portfolio in config['portfolios']:
        if portfolio.name == portfolio_name:
            portfolio.products.append(product)
    bucket.put_config(config, CONFIG_PREFIX)
    return product


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
