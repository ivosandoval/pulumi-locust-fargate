import pulumi
from pulumi_aws import route53, acm, provider

config = pulumi.Config()
DOMAIN = config.require('domain')

# Route53 Zone
zone = route53.Zone(
    resource_name=f'{pulumi.get_project()}-zone',
    name=DOMAIN,
    comment=f'Main DNS record for `{pulumi.get_project()}` project',
    tags=None,
    # Destroy records in order to destroy zone ?
    force_destroy=False,
    opts=pulumi.ResourceOptions(
        protect=True
    )
)
pulumi.export('zone_ns', zone.name_servers)
pulumi.export('zone_name', zone.name)
pulumi.export('zone_id', zone.zone_id)

# ACM Certificate

# Should be in "us-east-1" in order to work with Cloudfront
# https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cnames-and-https-requirements.html#https-requirements-aws-region
aws_us_east = provider.Provider("aws", region="us-east-1")

certificate = acm.Certificate(
    resource_name=f'{pulumi.get_project()}-certificate',
    domain_name=DOMAIN,
    subject_alternative_names=[
        f'*.{DOMAIN}'
    ], 
    tags=None, 
    validation_method='DNS',
    opts=pulumi.ResourceOptions(
        protect=True,
        provider=aws_us_east
    )
)
pulumi.export('certificate_validation_options', certificate.domain_validation_options)

def deduplicate_validation_options(certificate_validation_options):
    """
    Deduplicates certificate validation options in order to come up with a set
    of records to create.

    Sample Certificate validation options:
    [
        {
            'domain_name': 'mydomain.com', 
            'resourceRecordName': '_ffddbd35ed5661e66c928d1a09738304.mydomain.com.', 
            'resourceRecordValue': '_f8cf4d66dc5190774209623c835578e0.mzlfeqexyx.acm-validations.aws.', 
            'resourceRecordType': 'CNAME'
        },
        {
            'domain_name': '*.mydomain.com'
            'resourceRecordName': '_ffddbd35ed5661e66c928d1a09738304.mydomain.com.',
            'resourceRecordValue': '_f8cf4d66dc5190774209623c835578e0.mzlfeqexyx.acm-validations.aws.', 
            'resourceRecordType': 'CNAME', 
        }
    ]
    """
    records = {}
    for o in certificate_validation_options:
        records[o['resourceRecordName']] = o['resourceRecordValue']
    return records
records_to_create = certificate.domain_validation_options\
        .apply(deduplicate_validation_options)
pulumi.export('records_to_create', records_to_create)


record = route53.Record(
    resource_name=f'{pulumi.get_project()}-certificate-validation-record',
    name=certificate.domain_validation_options[0]['resourceRecordName'],
    records=[certificate.domain_validation_options[0]['resourceRecordValue']],
    ttl=300,
    type=certificate.domain_validation_options[0]['resourceRecordType'],
    zone_id=zone.zone_id,
)

validation = acm.CertificateValidation(
    resource_name=f'{pulumi.get_project()}-certificate-validation',
    certificate_arn=certificate.arn,
    validation_record_fqdns=[record.fqdn],
    opts=pulumi.ResourceOptions(
        provider=aws_us_east
    )
)