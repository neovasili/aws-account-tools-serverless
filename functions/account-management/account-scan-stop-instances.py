import json
import boto3
import os
import datetime

region = os.environ[ 'region' ]
stop_lambda_function = os.environ[ 'stop_lambda_function' ]

def handler( event, context ):
    ec2 = boto3.client( 'ec2' )
    regions = ec2.describe_regions()
    
    now = datetime.datetime.now()

    currentHour = now.hour
    response = {
        "statusCode": 200,
        "body": []
    }

    for region in regions[ 'Regions' ]:
        regionName = region[ 'RegionName' ]
        ec2 = boto3.client( 'ec2', region_name=regionName )
        instances_to_stop = []

        filters = [ 
            {
                'Name':'tag:stop', 'Values':[ str( currentHour ) ]
            },
            {
                'Name':'instance-state-name', 'Values':[ 'running' ]
            } 
        ]

        reservations = ec2.describe_instances( Filters=filters )[ 'Reservations' ]

        for reservation in reservations:
            instances = reservation[ 'Instances' ]

            for instance in instances:
                instances_to_stop.append( instance[ 'InstanceId' ] )

        if instances_to_stop:
            payload = {
                "region": regionName,
                "instances": instances_to_stop
            }
            response[ 'body' ].append( payload )

            '''
            lambda_client = boto3.client( 'lambda' )
            lambda_client.invoke( 
                FunctionName=stop_lambda_function,
                InvocationType='Event',
                LogType='None',
                Payload=json.dumps( payload )
            )
            '''

    return response