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
    @cmdln.option("-s", "--stackname",
                  help="The stack name when provisioning a prouct.")
    def do_product(self, subcmd, opts, action):
        """
        ${cmd_name}: Product management for the masses!

        ${cmd_usage}
        Actions:
            create
            update
            delete
            list
            associate
            provision

        ${cmd_option_list}
        """
        actions = [
            'create',
            'update',
            'delete',
            'list',
            'associate',
            'provision',
            'terminate'
        ]
        if action not in actions:
            raise ValueError("Not a valid action: {}".format(action))
        if action == 'create':
            conduit.new_product(opts.name, opts.description, opts.cfntype, opts.portfolio)
        elif action == 'update':
            conduit.update_product(opts.id, opts.name, opts.description, opts.cfntype)
        elif action == 'delete':
            conduit.delete_product(opts.id, None)
        elif action == 'list':
            conduit.list_products()
        elif action == 'associate':
            conduit.associate_product_with_portfolio(opts.id, opts.portfolio)
        elif action == 'provision':
            conduit.provision_product(opts.id, opts.name, opts.stackname)
        elif action == 'terminate':
            conduit.terminate_provisioned_product(opts.id, opts.stackname)
        else:
            print("{}: not a valid action for product".format(action))

    @cmdln.option("-p", "--product",
                  help="The name of the product to build.")
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
        if action and action[0] == 'major':
            print("Releasing new major version...")
            conduit.build('major', opts.product)
        elif action and action[0] == 'minor':
            print("Releasing new minor version...")
            conduit.build('minor', opts.product)
        elif action and action[0] == 'patch':
            print("Release new patch version...")
            conduit.build('patch', opts.product)
        else:
            print("Release new build version...")
            conduit.build('build', opts.product)

    @cmdln.option("-p", "--product",
                  help="The name of the product to provision.")
    @cmdln.option("-n", "--name",
                  help="A name to assign to the provisioned product.")
    def do_provision(self, subcmd, opts):
        """
        ${cmd_name}: Provision a product from a conduitspec.yaml

        ${cmd_usage}
        ${cmd_option_list}
        """
        conduit.provision_product_build(opts.product, opts.name)

    @cmdln.option("-n", "--name",
                  help="A name to assign to the provisioned product.")
    def do_terminate(self, subcmd, opts):
        """
        ${cmd_name}: Terminate a product from a conduitspec.yaml

        ${cmd_usage}
        ${cmd_option_list}
        """
        conduit.terminate_product(opts.name)

    def do_sync(seld, subcmd, opts):
        """
        ${cmd_name}: Ensure conduit is up to date.

        ${cmd_usage}
        ${cmd_option_list}
        """
        conduit.sync()

    @cmdln.option("-p", "--portfolio",
                  help="The name of the portfolio to package.")
    @cmdln.option("-e", "--environment",
                  help="The environment to package.")
    def do_package(self, subcmd, opts):
        conduit.package_portfolio(opts.portfolio, opts.environment)

    @cmdln.option("-p", "--portfolio",
                  help="The name of the portfolio to package.")
    @cmdln.option("-d", "--product",
                  help="The name of the product to package.")
    @cmdln.option("-e", "--environment",
                  help="The environment to package.")
    def do_package_product(self, subcmd, opts):
        conduit.package_product(opts.portfolio, opts.product, opts.environment)


def main():
    aws_conduit = Conduit()
    sys.exit(aws_conduit.main())
