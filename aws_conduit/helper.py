import boto3

from aws_conduit import conduit_factory as factory

SESSION = boto3.session.Session()
IAM = boto3.client('iam')
STS = boto3.client('sts')

CONFIG_PREFIX = 'conduit.yaml'


def get_region():
    region = SESSION.region_name
    return region


def get_account_id():
    account_id = STS.get_caller_identity().get('Account')
    return account_id


def get_alias():
    """
    Get the users account alias.

    Return:
        alias: The first known account alias.
    """
    aliases = IAM.list_account_aliases()
    if aliases and aliases['AccountAliases']:
        return aliases['AccountAliases'][0]


def get_portfolio(config, name=None, portfolio_id=None):
    for portfolio in config['portfolios']:
        if name is not None:
            if portfolio.name == name:
                return portfolio
        if portfolio_id is not None:
            if portfolio.portfolio_id == portfolio_id:
                return portfolio
    raise ValueError('Portfolio not found: {} {}'.format(portfolio_id, name))


def get_product(config, name=None, product_id=None):
    for portfolio in config['portfolios']:
        for product in portfolio.products:
            if product_id is not None:
                if product.product_id == product_id:
                    return product
            if name is not None:
                if product.name == name:
                    return product
    raise ValueError('Product not found: {} {}'.format(product_id, name))


ACCOUNT_ID = get_account_id()


def inject_config(function):

    start = factory.start()
    bucket = start.create_s3()
    configuration = bucket.get_config(CONFIG_PREFIX)

    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs, config=configuration)
        bucket.put_config(configuration, CONFIG_PREFIX)
        return result

    return wrapper


def find_build_product(to_find_product, spec, config):
    portfolio = None
    product = None
    for port in config['portfolios']:
        if port.name == spec['portfolio']:
            portfolio = port
            for prod in portfolio.products:
                if prod.name == to_find_product:
                    product = prod
                    break
    if portfolio is None or not portfolio.exists():
        raise ValueError("The specified portfolio does not exist: {}".format(to_find_product))
    elif product is None or not product.exists():
        raise ValueError("The product {} does not exist in portfolio {}".format(to_find_product, spec['portfolio']))
    return product


def find_provisioned_build_product(to_find_product, spec, config):
    portfolio = None
    product = None
    for port in config['portfolios']:
        if port.name == spec['portfolio']:
            portfolio = port
            for prod in portfolio.products:
                if hasattr(prod, provisioned):
                    for prov in prod.provisioned:
                        if prov == to_find_product:
                            product = prod
                            break

    if portfolio is None or not portfolio.exists():
        raise ValueError("The specified portfolio does not exist: {}".format(to_find_product))
    elif product is None or not product.exists():
        raise ValueError("The product {} does not exist in portfolio {}".format(to_find_product, spec['portfolio']))
    return product
