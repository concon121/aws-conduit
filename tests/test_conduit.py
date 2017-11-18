import time

import boto3
import pytest

from aws_conduit import conduit, conduit_factory

STS = boto3.client('sts')
ACCOUNT_ID = STS.get_caller_identity().get('Account')
BUCKET_NAME = 'conduit-config-' + ACCOUNT_ID


def test_configure():
    bucket = conduit.configure()
    assert bucket.exists()
    bucket.delete()
    assert not bucket.exists()


def test_configure_bucket_already_exists():
    bucket = conduit.configure()
    conduit.configure()
    assert bucket.exists()
    bucket.delete()
    assert not bucket.exists()


def test_new_portfolio():
    portfolio_name = "TestPortfolio"
    portfolio = conduit.new_portfolio(
        name=portfolio_name,
        description="This is a test portfolio"
    )
    assert portfolio.exists()
    portfolio.delete()
    assert not portfolio.exists()
    bucket = conduit.configure()
    bucket.delete()


def test_new_portfolio_without_name():
    with pytest.raises(ValueError):
        conduit.new_portfolio(
            name=None,
            description="This is a test portfolio"
        )


def test_new_product():
    product_name = "TestProduct"
    portfolio_name = "TestPortfolio"
    portfolio = conduit.new_portfolio(
        name=portfolio_name,
        description="This is a test portfolio"
    )
    product = conduit.new_product(
        name=product_name,
        description="This is a test portfolio",
        cfntype="yaml",
        portfolio_name=portfolio_name
    )
    product.delete()
    portfolio.delete()
    bucket = conduit.configure()
    bucket.delete()


def test_set_default_support_config():
    description = "This is the default support settings"
    email = "noone@home.com"
    url = "http://madeup.com"
    bucket = conduit.configure()
    conduit.set_default_support_config(
        description=description,
        email=email,
        url=url
    )
    config = bucket.get_config(conduit.CONFIG_PREFIX)
    print(config)
    assert config['support'] is not None
    assert config['support']['description'] == description
    assert config['support']['url'] == url
    assert config['support']['email'] == email
    bucket.delete()


def test_set_default_support_config_with_missing_details():
    description = "This is the default support settings"
    email = "noone@home.com"
    url = "http://madeup.com"
    bucket = conduit.configure()
    conduit.set_default_support_config(
        description=description
    )
    config = bucket.get_config(conduit.CONFIG_PREFIX)
    print(config)
    assert config['support'] is not None
    assert config['support']['description'] == description
    assert 'url' not in config['support']
    assert 'email' not in config['support']
