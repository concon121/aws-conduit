import sys

import cmdln

from aws_conduit import conduit


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
    @cmdln.option("-i", "--id",
                  help="The portfolio id for use on an update.")
    def do_portfolio(self, subcmd, opts, action):
        """
        ${cmd_name}: Portfolio management for the masses!

        ${cmd_usage}
        Actions:
            create
            update
            delete
            list

        ${cmd_option_list}
        """
        actions = [
            'create',
            'update',
            'delete',
            'list'
        ]
        if action not in actions:
            raise ValueError("Not a valid action: {}".format(action))
        if action == 'create':
            conduit.new_portfolio(opts.name, opts.description)
        elif action == 'update':
            conduit.update_portfolio(opts.id, opts.name, opts.description)
        elif action == 'delete':
            conduit.delete_portfolio(opts.id)
        elif action == 'list':
            conduit.list_portfolios()
        else:
            print("{}: not a valid action for portfolio".format(action))

    @cmdln.option("-n", "--name",
                  help="The name of the portfolio.")
    @cmdln.option("-d", "--description",
                  help="Information about the product.")
    @cmdln.option("-c", "--cfntype",
                  help="yaml or json?")
    @cmdln.option("-p", "--portfolio",
                  help="The name of the portfolio.")
    @cmdln.option("-i", "--id",
                  help="The product id for use on an update.")
    def do_product(self, subcmd, opts, action):
        """
        ${cmd_name}: Product management for the masses!

        ${cmd_usage}
        Actions:
            create
            update
            delete
            list

        ${cmd_option_list}
        """
        actions = [
            'create',
            'update',
            'delete',
            'list'
        ]
        if action not in actions:
            raise ValueError("Not a valid action: {}".format(action))
        if action == 'create':
            conduit.new_product(opts.name, opts.description, opts.cfntype, opts.portfolio)
        elif action == 'update':
            conduit.update_product(opts.id, opts.name, opts.description, opts.cfntype)
        elif action == 'delete':
            conduit.delete_product(opts.id)
        elif action == 'list':
            conduit.list_products()
        else:
            print("{}: not a valid action for product".format(action))

    def do_build(self, subcmd, opts, *action):
        """
        ${cmd_name}: Release a build from a conduitspec.yaml

        ${cmd_usage}
        Actions:
            major
            minor
            patch

        ${cmd_option_list}
        """
        conduit.build()


def main():
    aws_conduit = Conduit()
    sys.exit(aws_conduit.main())
