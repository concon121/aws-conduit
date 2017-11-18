"""Helper methods for working with Service Catalog Portfolios."""
import attr
import boto3
import yaml


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
            name (str): The display name of the new portfolio
            description (str): A brief description of the portfolio
            alias (str): The account alias to use as the portfolio provider
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
        Delete a Service Catalog portfolio by its display name.

        Args:
            name (str): The display name of the portfolio to delete.
        """
        portfolio_id = self.get_id()
        print(portfolio_id)
        self.service_catalog.delete_portfolio(
            Id=portfolio_id
        )

    def exists(self, token=None):
        """
        Test if a portfolio exists by its display name.

        Args:
            name (str): The display name of the portfolio to test for.
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
        Get the id of a portfolio by its display name.

        Args:
            name (str): The display name of the portfolio to test for.
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
