
import json

import boto3
from aws_conduit import helper

IAM = boto3.client('iam')

BASIC_POLICY = {
    'Statement': [
        {
            'Principal': {
                'AWS': helper.get_account_id()
            },
            'Effect': 'Allow',
            'Action': ['sts:AssumeRole']
        }, {
            'Principal': {
                'Service': 'servicecatalog.amazonaws.com'
            },
            'Effect': 'Allow',
            'Action': ['sts:AssumeRole']
        }
    ]
}


def create_role(name, description):
    response = IAM.create_role(
        Path='/conduit/',
        RoleName=name,
        AssumeRolePolicyDocument=json.dumps(BASIC_POLICY),
        Description=description
    )
    return response['Role']


def add_policy(role_name, policy_name):
    IAM.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/{}'.format(policy_name)
    )


def list_roles(prefix):
    response = IAM.list_roles(
        PathPrefix=prefix
    )
    return response['Roles']


def put_role_policy(role_name, policy_name, policy):
    IAM.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy)
    )
