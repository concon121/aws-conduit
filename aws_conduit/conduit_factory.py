import boto3

from aws_conduit import helper
from aws_conduit.conduit_portfolio import ConduitPortfolio
from aws_conduit.conduit_product import ConduitProduct
from aws_conduit.conduit_role import ConduitRole
from aws_conduit.conduit_s3 import ConduitS3
from aws_conduit.conduit_start import ConduitStart

SESSION = boto3.session.Session()
REGION = SESSION.region_name


def start():
    account_id = helper.ACCOUNT_ID
    return ConduitStart(account_id)


def s3(name):
    """
    Creates a new handle for an S3 bucket.

    Args:
        name (str): The name of the S3 bucket.

    Return:
        ConduitS3 (obj): An unpersisted instance of an S3 bucket.
    """
    return ConduitS3(name, REGION)


def portfolio(portfolio_name, portfolio_description=None):
    """
    Creates a new handle for a Service Catalog portfolio.

    Args:
        portfolio_name (str): The name to aply to the Portfolio.
        portfolio_provider (str): The name of the Portfolio provider.
        portfolio_description (str): Information about the Portfolio.

    Return:
        ConduitPortfolio: An unpersistened instance of a Portfolio.
    """
    portfolio_provider = helper.get_alias()
    return ConduitPortfolio(
        name=portfolio_name,
        description=portfolio_description,
        provider=portfolio_provider
    )


def product_by_id(product_id, token=None):
    client = boto3.client('servicecatalog')
    if token is not None:
        response = client.search_products_as_admin(
            PageToken=token
        )
    else:
        response = client.search_products_as_admin()
    if response['ProductViewDetails']:
        for found_product in response['ProductViewDetails']:
            if found_product['ProductViewSummary']['ProductId'] == product_id:
                print("Creating instance of Conduit handle...")
                summary = found_product['ProductViewSummary']
                conduit_product = product(summary['Name'], None, summary['ShortDescription'])
                conduit_product.product_id = product_id
                return conduit_product
    if 'NextPageToken' in response:
        return product_by_id(product_id, token=response['NextPageToken'])


def product(product_name, portfolio_name, product_description=None):
    """
    Creates a new handle for a Service Catalog Product.

    Args:
        product_name (str): The name of the Product.
        product_owner (str): The owner of the product.
        s3_bucket (obj): A Conduit handle on an S3 Bucket.
        cfntype (str): yaml or json.
        portfolio_name (str): The Portfolio which this Product can be applied to.
        product_description (str): Information about the product.

    Return:
        ConduitProduct: An unpersisted instance of a Product.
    """
    product_owner = helper.get_alias()
    s3_bucket = start().create_s3()
    cfntype = "yaml"
    return ConduitProduct(
        name=product_name,
        owner=product_owner,
        bucket=s3_bucket,
        cfn_type=cfntype,
        portfolio=portfolio_name,
        description=product_description
    )


def role(role_name):
    role = ConduitRole(role_name)
    return role
