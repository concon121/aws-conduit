# AWS Conduit

Product management for AWS Service Catalog.

## Installation

TODO - AWS Conduit will be available to install via pip.

```
pip install aws_conduit
```

## Usage

### Overview

#### Core
```
> conduit ?

Usage:
    conduit COMMAND [ARGS...]
    conduit help [COMMAND]

Options:
    -h, --help  show this help message and exit

Commands:
    help (?)       give detailed help on a specific sub-command
    start          ${cmd_name}: Set up the initial Conduit resources.
    support        ${cmd_name}: Set the default support configuration.
```
#### Start
```
> conduit help start

start: Set up the initial Conduit resources.

Usage:
    conduit start
```

#### Support
```
> conduit help support

support: Set the default support configuration.

Usage:
    conduit support

Options:
    -h, --help          show this help message and exit
    -d DESCRIPTION, --description=DESCRIPTION
                        Support information about the product.
    -u URL, --url=URL   Contact URL for product support.
    -e EMAIL, --email=EMAIL
                        Contact email for product support.
```

#### Portfolio
```
> conduit help portfolio

portfolio: Portfolio management for the masses!

Usage:
    conduit portfolio ACTION

Actions:
    create

Options:
    -h, --help          show this help message and exit
    -d DESCRIPTION, --description=DESCRIPTION
                        Information about the portfolio.
    -n NAME, --name=NAME
                        The name of the portfolio.
```

#### Product
```
> conduit help product

product: Product management for the masses!

Usage:
    conduit product ACTION

Actions:
    create

Options:
    -h, --help          show this help message and exit
    -p PORTFOLIO, --portfolio=PORTFOLIO
                        The name of the portfolio.
    -c CFNTYPE, --cfntype=CFNTYPE
                        yaml or json?
    -d DESCRIPTION, --description=DESCRIPTION
                        Information about the product.
    -n NAME, --name=NAME
                        The name of the portfolio.
```

### Where do I start?

AWS conduit needs to set up an S3 bucket which is used to store configuration and cloudformation resources. This bucket will be named ```conduit-config-${AWS::AccountId}```.

Once the S3 bucket is in place, the default support configuration for your products should be set.

```
> conduit start
> conduit support --email "noone@home.com" --url "http://madeup.com" --description "This is the groovy support info"
```

### Conduit by Example

#### Creating a new Portfolio

```
> conduit portfolio create --n "My Portfolio" --d "This is my portfolio description"
```

#### Creating a new Product
```
> conduit product create -n "My Product" -d "this is my product info" -c "yaml" -p "My Portfolio"
```

#### CI Build Increment
```
> conduit build
```

#### List all Portfolios
```
> conduit portfolio list
Name                          Id                            Description
------------------------------------------------------------------------------------------
test-portfolio                port-c3ghpcitagt2w            test portfolio description
another-portfolio             port-dfh2m6vzbwweu            groovy portfolio
```

#### List all products
```
> conduit product list
Name                          Id                            Description
------------------------------------------------------------------------------------------
groovy-test-product           prod-wkc4otel6chxu            Groovy products are groovy
another-test-product          prod-craeqnatjljsc            Another test product
```
