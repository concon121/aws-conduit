# AWS Conduit

Product management for AWS Service Catalog.

## Installation

AWS Conduit is available to install via pip.

```
pip install aws_conduit
```

## Usage
```
> conduit ?

Usage:
    conduit COMMAND [ARGS...]
    conduit help [COMMAND]

Options:
    -h, --help  show this help message and exit


Commands:
    build          Release a build from a conduitspec.yaml
    help (?)       give detailed help on a specific sub-command
    portfolio      Portfolio management for the masses!
    product        Product management for the masses!
    provision      Provision a product from a conduitspec.yaml
    start          Set up the initial Conduit resources.
    support        Set the default support configuration.
    terminate      Terminate a product from a conduitspec.yaml
```

## Tutorial

### Initial Setup

AWS conduit needs to set up some intial resources to get started.

#### Whats in the box?
* An S3 bucket which is used to store configuration and cloudformation resources. This bucket will be named ```conduit-config-${AWS::AccountId}```.
* An IAM role which deployments happen through.  This will be named ```conduit-provisioner-role```.
* An IAM policy which custom deploy profiles are added to.  This will be named ```conduit-policy```.

```
> conduit start
```

### Support Details

Service Catalog products can have support information assigned to them.  This is so that if anything goes wrong with your products, your users know how to contact you!

```
> conduit support -e "noone@home.com" -u "http://madeup.com" -d "This is the groovy support info"
```

### Creating a new Portfolio

You'll want to create a new portfolio before you start adding new products.  A portfolio is a collection of products that can be shared with other users and other AWS accounts.

```
> conduit portfolio create -n "My Portfolio" -d "This is my portfolio description"
```

### Creating a new Product

When you have a portfolio in place, start adding new products to it!

```
> conduit product create -n "My Product" -d "this is my product info" -c "yaml" -p "My Portfolio"
```

### The conduitspec.yaml

The aim of this file is to behave as a descriptor of your product, facilitating automation of builds and deployments by proving Conduit with an appropriate set of metadata.

#### Example coduitspec.yaml

```
portfolio: "test-portfolio"      # The name of the portfolio this product belongs to.
product: "groovy-test-product"   # The name of this product.
cfn:                             # Cloudformation information
  template: "TestProduct.yaml"   # The location of the cloudformation template relative to the current directory.
  type: "yaml"                   # yaml or json
deployProfile:                   # Custom IAM policy which describes the actions are resources involved
  - actions:                     # in deployment of your product.
      - "s3:*"
    resources:
      - "*"
```

### CI Build Increments

When using a conduitspec.yaml, product changes can be published via semantic versioning of your release artifacts.

The build command will create a new artifact version in Service Catalog, of the product defined by the conduitspec.yaml.

```
                         # Starting on version 0.0.0
> conduit build          # 0.0.0+build1
> conduit build          # 0.0.0+build2
> conduit build          # 0.0.0+build3
> conduit build patch    # 0.0.1
> conduit build patch    # 0.0.2
> conduit build          # 0.0.2+build1
> conduit build minor    # 0.1.0
> conduit build major    # 1.0.0
```

Build versions (+build...) are considered to be temporary.  Upon release of a major / minior / patch version, all build versions that are lower than the new version are removed from Service Catalog, so your product version history is kept nice and tidy!

### Provisioning

When using a conduitspec.yaml, you can provision and terminate your product on the cli, all you need to do is provide a name for the provisioned product.  In a CI environment, it is recommended that the name you provide reflects the environment you are deploying to.

NOTE: At the time of writing, stack parameters are input on the command line.  This is not particularly automation friendly and will be improved in the near future.

#### Example Provisioner

```
> conduit provision -n test-product-dev
Account Id: 12345678910
Ensuring Conduit is up to date...
Associating conduit with test-portfolio
Associating conduit with example-port
Provisioning product...
Getting launch path...
Getting input parameters...
Hello (Default: World!): yolo!
Assumiing conduit IAM role...
Provisioning now...
Provision Success!
```

#### Example Terminator

```
conduit terminate -n test-product-dev
Account Id: 12345678910
Ensuring Conduit is up to date...
Associating conduit with test-portfolio
Associating conduit with example-port
Terminating product...
Assumiing consuit IAM role...
Terminating now...
Terminate complete!
```

#### Example Updater

If you release a new version of a product after provisioning it, re-provisioning will automatically perform an update for you.

```
> conduit provision -n test-product-dev
Account Id: 12345678910
Ensuring Conduit is up to date...
Associating conduit with test-portfolio
Associating conduit with example-port
Provisioning product...
Getting launch path...
Getting input parameters...
Hello (Default: World!): yolo!
Assumiing conduit IAM role...
Updating now...
Update Success!
```

### Utility Commands

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

## Best Practices

* conduitspec.yaml is king!  Yes, you can do stuff without it, but life will be easier if you embrace it.
