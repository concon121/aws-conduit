from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    include_package_data=True,
    name='aws_conduit',
    packages=['aws_conduit'],
    version='0.0.1',
    description='Product management for AWS Service Catalog.',
    author='Connor Bray',
    author_email='connor.bray@icloud.com',
    install_requires=required,
    entry_points={
        'console_scripts': [
            'conduit=aws_conduit.__init__:main'
        ]
    }
)
