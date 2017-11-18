import attr
import boto3
import yaml


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
    template_location = attr.ib(default=None)
    template_prefix = attr.ib(default=None)
    product_id = attr.ib(default=None)
    service_catalog = boto3.client('servicecatalog')

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
        if not self.template_location:
            self.template_location = "{}/{}/{}.{}".format(self.bucket.get_url(), self.portfolio, self.name, self.cfn_type)
            self.template_prefix = "{}/{}.{}".format(self.portfolio, self.name, self.cfn_type)
        self._add_initial_template()
        create_response = self.service_catalog.create_product(
            Name=self.name,
            Owner=self.owner,
            Description=self.description,
            Distributor=self.owner,
            SupportDescription=support['description'],
            SupportEmail=support['email'],
            SupportUrl=support['url'],
            ProductType='CLOUD_FORMATION_TEMPLATE',
            Tags=tags,
            ProvisioningArtifactParameters={
                'Name': '0.0.0',
                'Description': 'Initial product creation.',
                'Info': {
                    'LoadTemplateFromURL': self.template_location
                },
                'Type': 'CLOUD_FORMATION_TEMPLATE'
            },
        )
        self.product_id = create_response['ProductViewDetail']['ProductViewSummary']['ProductId']

    def add_to_portfolio(self, portfolio_id):
        # if not self.product_id:
        self.set_product_id()
        self.service_catalog.associate_product_with_portfolio(
            ProductId=self.product_id,
            PortfolioId=portfolio_id
        )

    def set_product_id(self):
        if self.product_id is None:
            summary = self.get_summary()
            self.product_id = summary['ProductId']

    def get_summary(self):
        response = self.service_catalog.search_products_as_admin(
            Filters={
                'FullTextSearch': [
                    self.name,
                ]
            }
        )
        print(response)
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
        print(summary)
        return bool(summary is not None)

    def delete(self):
        self.set_product_id()
        portfolios = self.get_all_portfolios()
        for portfolio in portfolios:
            self.disassociate(portfolio)
        self.service_catalog.delete_product(
            Id=self.product_id
        )

    def disassociate(self, portfolio):
        self.service_catalog.disassociate_product_from_portfolio(
            ProductId=self.product_id,
            PortfolioId=portfolio
        )

    def get_all_portfolios(self, token=None):
        self.set_product_id()
        if token:
            response = self.service_catalog.list_portfolios_for_product(
                ProductId=self.product_id,
                PageToken=token,
            )
        else:
            response = self.service_catalog.list_portfolios_for_product(
                ProductId=self.product_id
            )
        portfolios = [item['Id'] for item in response['PortfolioDetails']]
        if 'NextPageToken' in response:
            portfolios = portfolios + self.get_all_portfolios(token=response['NextPageToken'])
        return portfolios
