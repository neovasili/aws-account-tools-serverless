import json
import boto3
import os

def handler( event, context ):

    region = event[ 'region' ]
    instances = event[ 'instances' ]

    ec2 = boto3.client( 'ec2', region_name=region )
    ec2.start_instances( InstanceIds=instances )

    response = {
        "statusCode": 200,
        "body": 'STARTED instances: ' + str( instances )
    }

    return response