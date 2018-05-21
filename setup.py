from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    include_package_data=True,
    name='aws_conduit',
    packages=['aws_conduit', 'aws_conduit.aws'],
    version='0.0.31',
    description='Product management for AWS Service Catalog.',
    author='Connor Bray',
    author_email='connor.bray@icloud.com',
    url="https://github.com/concon121/aws-conduit",
    download_url="https://github.com/concon121/aws-conduit/archive/0.0.31.tar.gz",
    install_requires=required,
    keywords=['aws', 'servicecatalog'],
    entry_points={
        'console_scripts': [
            'conduit=aws_conduit.__init__:main'
        ]
    }
)
