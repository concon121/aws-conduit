import sys

import cmdln

from aws_conduit import conduit


class Portfolio(cmdln.Cmdln):

    name = "portfolio"

    @cmdln.option("-n", "--name",
                  help="Portfolio name.")
    @cmdln.option("-d", "--description",
                  help="Portfolio description.")
    def do_create(self, subcmd, opts):
        """
        ${cmd_name}: Create a new portfolio.

        ${cmd_usage}
        """


class Conduit(cmdln.Cmdln):
    name = "conduit"

    def do_start(self, subcmd, opts):
        """
        ${cmd_name}: Set up the initial Conduit resources.

        ${cmd_usage}
        """
        conduit.configure()

    @cmdln.option("-e", "--email",
                  help="Contact email for product support.")
    @cmdln.option("-u", "--url",
                  help="Contact URL for product support.")
    @cmdln.option("-d", "--description",
                  help="Support information about the product.")
    def do_support(self, subcmd, opts):
        """
        ${cmd_name}: Set the default support configuration.

        ${cmd_usage}
        ${cmd_option_list}
        """
        conduit.set_default_support_config(
            description=opts.description,
            email=opts.email,
            url=opts.url
        )

    @cmdln.option("-n", "--name",
                  help="The name of the portfolio.")
    @cmdln.option("-d", "--description",
                  help="Information about the portfolio.")
    def do_portfolio(self, subcmd, opts, action):
        """
        ${cmd_name}: Portfolio management for the masses!

        ${cmd_usage}
        Actions:
            create

        ${cmd_option_list}
        """
        actions = [
            'create'
        ]
        if action not in actions:
            raise ValueError("Not a valid action: {}".format(action))
        if action == 'create':
            conduit.new_portfolio(opts.name, opts.description)

    @cmdln.option("-n", "--name",
                  help="The name of the portfolio.")
    @cmdln.option("-d", "--description",
                  help="Information about the product.")
    @cmdln.option("-c", "--cfntype",
                  help="yaml or json?")
    @cmdln.option("-p", "--portfolio",
                  help="The name of the portfolio.")
    def do_product(self, subcmd, opts, action):
        """
        ${cmd_name}: Product management for the masses!

        ${cmd_usage}
        Actions:
            create

        ${cmd_option_list}
        """
        actions = [
            'create'
        ]
        if action not in actions:
            raise ValueError("Not a valid action: {}".format(action))
        if action == 'create':
            conduit.new_product(opts.name, opts.description, opts.cfntype, opts.portfolio)


def main():
    aws_conduit = Conduit()
    sys.exit(aws_conduit.main())
