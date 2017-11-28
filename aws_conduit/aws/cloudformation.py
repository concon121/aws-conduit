import boto3

CFN = boto3.client('cloudformation')


def list_parameters(url):
    summary = CFN.get_template_summary(
        TemplateURL=url
    )
    if 'Parameters' in summary:
        return summary['Parameters']
    return []
