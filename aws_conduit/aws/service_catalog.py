import json

import boto3

SERVICE_CATALOG = boto3.client('servicecatalog')
ROW_FORMAT = "{:<30}" * 3


def associate(product_id, portfolio_id):
    SERVICE_CATALOG.associate_product_with_portfolio(
        ProductId=product_id,
        PortfolioId=portfolio_id
    )


def disassociate(product_id, portfolio):
    SERVICE_CATALOG.disassociate_product_from_portfolio(
        ProductId=product_id,
        PortfolioId=portfolio
    )


def create_constraint(portfolio_id, product_id, params, name):
    SERVICE_CATALOG.create_constraint(
        PortfolioId=portfolio_id,
        ProductId=product_id,
        Parameters=json.dumps(params),
        Type='LAUNCH',
        Description='Launch configuration for {}'.format(name)
    )


def create_product(product, support_email, support_url, support_description, tags, template):
    create_response = SERVICE_CATALOG.create_product(
        Name=product.name,
        Owner=product.owner,
        Description=product.description,
        Distributor=product.owner,
        SupportDescription=support_description,
        SupportEmail=support_email,
        SupportUrl=support_url,
        ProductType='CLOUD_FORMATION_TEMPLATE',
        Tags=tags,
        ProvisioningArtifactParameters={
            'Name': '0.0.0',
            'Description': 'Initial product creation.',
            'Info': {
                'LoadTemplateFromURL': template
            },
            'Type': 'CLOUD_FORMATION_TEMPLATE'
        },
    )
    return create_response


def list_all_portfolios(token=None):
    if token is not None:
        response = SERVICE_CATALOG.list_portfolios(
            PageToken=token
        )
    else:
        response = SERVICE_CATALOG.list_portfolios()
    for portfolio in response['PortfolioDetails']:
        print(ROW_FORMAT.format(portfolio['DisplayName'], portfolio['Id'], portfolio['Description']))
    if 'NextPageToken' in response:
        list_all_portfolios(token=response['NextPageToken'])


def list_portfolios_for_product(product_id, token=None):
    if token:
        response = SERVICE_CATALOG.list_portfolios_for_product(
            ProductId=product_id,
            PageToken=token,
        )
    else:
        response = SERVICE_CATALOG.list_portfolios_for_product(
            ProductId=product_id
        )
    portfolios = [item['Id'] for item in response['PortfolioDetails']]
    if 'NextPageToken' in response:
        portfolios = portfolios + list_portfolios_for_product(product_id, token=response['NextPageToken'])
    return portfolios


def list_all_products(token=None):
    if token is not None:
        response = SERVICE_CATALOG.search_products_as_admin(
            PageToken=token
        )
    else:
        response = SERVICE_CATALOG.search_products_as_admin()
    for product in response['ProductViewDetails']:
        summary = product['ProductViewSummary']
        print(ROW_FORMAT.format(summary['Name'], summary['ProductId'], summary['ShortDescription']))
    if 'NextPageToken' in response:
        list_all_products(token=response['NextPageToken'])


def list_product_constraints(portfolio_id, product_id):
    response = SERVICE_CATALOG.list_constraints_for_portfolio(
        PortfolioId=portfolio_id,
        ProductId=product_id
    )
    return response['ConstraintDetails']


def get_provisioning_parameters(product_id, version_id, launch_path):
    response = SERVICE_CATALOG.describe_provisioning_parameters(
        ProductId=product_id,
        ProvisioningArtifactId=version_id,
        PathId=launch_path
    )
    return response['ProvisioningArtifactParameters']


def get_all_launch_paths(product_id):
    launch_paths = SERVICE_CATALOG.list_launch_paths(
        ProductId=product_id,
    )
    return launch_paths['LaunchPathSummaries']


def search(term):
    response = SERVICE_CATALOG.search_products_as_admin(
        Filters={
            'FullTextSearch': [
                term,
            ]
        }
    )
    return response


def update_product(product_id, name, owner, description, support_description, support_url, support_email):
    SERVICE_CATALOG.update_product(
        Id=product_id,
        Name=name,
        Owner=owner,
        Description=description,
        Distributor=owner,
        SupportDescription=support_description,
        SupportEmail=support_email,
        SupportUrl=support_url,
    )


def delete_version(product_id, version_id):
    SERVICE_CATALOG.delete_provisioning_artifact(
        ProductId=product_id,
        ProvisioningArtifactId=version_id
    )


def list_all_versions(product_id):
    response = SERVICE_CATALOG.list_provisioning_artifacts(
        ProductId=product_id
    )
    return response['ProvisioningArtifactDetails']


def new_version(product_id, name, template_url):
    print(template_url)
    description = 'Release Candidate build increment'
    if 'build' in name:
        description = 'Incremental build; Not production ready!'
    SERVICE_CATALOG.create_provisioning_artifact(
        ProductId=product_id,
        Parameters={
            'Name': name,
            'Description': description,
            'Info': {
                'LoadTemplateFromURL': template_url
            },
            'Type': 'CLOUD_FORMATION_TEMPLATE'
        }
    )


def provision(client, product, name, params):
    client.provision_product(
        ProductId=product.product_id,
        ProvisioningArtifactId=product.get_version_id(),
        ProvisionedProductName=name,
        ProvisioningParameters=params
    )


def update_provisioned(client, product, name, params):
    client.update_provisioned_product(
        ProvisionedProductName=name,
        ProductId=product.product_id,
        ProvisioningArtifactId=product.get_version_id(),
        ProvisioningParameters=params
    )


def terminate_provisioned(client, name):
    client.terminate_provisioned_product(
        ProvisionedProductName=name,
        IgnoreErrors=False
    )


def is_provisioned(name, token=None):
    if token:
        response = SERVICE_CATALOG.scan_provisioned_products(
            PageToken=token
        )
    else:
        response = SERVICE_CATALOG.scan_provisioned_products(
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
        return is_provisioned(name, token=response['NextPageToken'])
    return False
