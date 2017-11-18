import boto3

from aws_conduit.conduit_portfolio import ConduitPortfolio
from aws_conduit.conduit_product import ConduitProduct
from aws_conduit.conduit_s3 import ConduitS3

SESSION = boto3.session.Session()
REGION = SESSION.region_name


def s3(name):
    return ConduitS3(name, REGION)


def portfolio(product_name, product_provider, portfolio_description=None):
    return ConduitPortfolio(
        name=product_name,
        description=portfolio_description,
        provider=product_provider
    )


def product(product_name, product_owner, s3_bucket, cfntype, portfolio_name, product_description=None):
    return ConduitProduct(
        name=product_name,
        owner=product_owner,
        bucket=s3_bucket,
        cfn_type=cfntype,
        portfolio=portfolio_name,
        description=product_description
    )
