"""Helper methods for working with Service Catalog Portfolios."""
import boto3
import yaml

import attr


@attr.s
class ConduitPortfolio(yaml.YAMLObject):
    """Portfolio helper class."""

    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Portfolio'
    name = attr.ib()
    provider = attr.ib()
    description = attr.ib(default='No description set')
    portfolio_id = attr.ib(default=None)
    products = attr.ib(default=[])
    service_catalog = boto3.client('servicecatalog')

    def create(self, tags):
        """
        Create a new Service Catalog portfolio.

        Args:
            tags (list): A list of tags to apply to the portfolio
        """
        response = self.service_catalog.create_portfolio(
            DisplayName=self.name,
            Description=self.description,
            ProviderName=self.provider,
            Tags=tags
        )
        self.portfolio_id = response['PortfolioDetail']['Id']

    def delete(self):
        """
        Delete this Service Catalog portfolio.
        """
        portfolio_id = self.get_id()
        print(portfolio_id)
        self.service_catalog.delete_portfolio(
            Id=portfolio_id
        )

    def update(self):
        """
        Update a service catalog protfolio.
        """
        self.service_catalog.update_portfolio(
            Id=self.portfolio_id,
            DisplayName=self.name,
            Description=self.description,
            ProviderName=self.provider
        )

    def exists(self, token=None):
        """
        Test if this portfolio exists.

        Args:
            token (str): (Optional) The NextPageToken returned by boto3.
        """
        portfolios = self._get_portfolio_list(token)
        if self.name in [portfolio['DisplayName'] for portfolio in portfolios['PortfolioDetails']]:
            return True
        elif 'NextPageToken' in portfolios:
            return self.exists(token=portfolios['NextPageToken'])
        return False

    def get_id(self, token=None):
        """
        Get the id of this portfolio.

        Args:
            token (str): (Optional) The NextPageToken returned by boto3.
        """
        if self.portfolio_id:
            return self.portfolio_id
        else:
            portfolios = self._get_portfolio_list(token)
            subset = [dict(
                name=portfolio['DisplayName'],
                id=portfolio['Id']
            ) for portfolio in portfolios['PortfolioDetails']]
            if self.name in [item['name'] for item in subset]:
                self.portfolio_id = next(item['id'] for item in subset if item['name'] == self.name)
                return self.portfolio_id
            elif 'NextPageToken' in portfolios:
                return self.get_id(token=portfolios['NextPageToken'])
            else:
                raise AttributeError('Portfolio was not found')

    def associate_conduit(self, account_id):
        response = self.service_catalog.associate_principal_with_portfolio(
            PortfolioId=self.portfolio_id,
            PrincipalARN='arn:aws:iam::{}:role/conduit/conduit-provisioner-role'.format(account_id),
            PrincipalType='IAM'
        )

    def _get_portfolio_list(self, token=None):
        if token:
            portfolios = self.service_catalog.list_portfolios(
                PageSize=20,
                PageToken=token
            )
        else:
            portfolios = self.service_catalog.list_portfolios(
                PageSize=20
            )
        return portfolios
