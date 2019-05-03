import json
import boto3
import os

def handler( event, context ):

    region = event[ 'region' ]
    instances = event[ 'instances' ]

    ec2 = boto3.client( 'ec2', region_name=region )
    ec2.stop_instances( InstanceIds=instances )

    response = {
        "statusCode": 200,
        "body": 'STOPPED instances: ' + str( instances )
    }

    return response