import boto3

SSM = boto3.client('ssm')


def get_param(key, environment):
    response = SSM.get_parameter(
        Name='{}-{}'.format(key, environment),
        WithDecryption=True
    )
    if 'Parameter' in response:
        return response['Parameter']['Value']
    return None
