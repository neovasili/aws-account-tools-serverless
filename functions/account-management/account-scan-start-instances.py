import json
import boto3
import os
import datetime
import pytz

stage = os.environ[ 'stage' ]
start_lambda_function = os.environ[ 'start_lambda_function' ]

def handler( event, context ):
    ec2 = boto3.client( 'ec2' )
    regions = ec2.describe_regions()
    
    europe = pytz.timezone( 'Europe/Madrid' )
    now = datetime.datetime.now().astimezone( europe )

    currentHour = now.hour
    response = {
        "statusCode": 200,
        "body": []
    }

    for region in regions[ 'Regions' ]:
        regionName = region[ 'RegionName' ]
        print( "currentHour: " + str( currentHour ) )
        print( "regionName: " + regionName )
        ec2 = boto3.client( 'ec2', region_name=regionName )
        instances_to_start = []

        filters = [ 
            {
                'Name':'tag:start', 'Values':[ str( currentHour ) ]
            },
            {
                'Name':'tag:stage', 'Values':[ stage ]
            },
            {
                'Name':'instance-state-name', 'Values':[ 'stopped' ]
            } 
        ]

        reservations = ec2.describe_instances( Filters=filters )[ 'Reservations' ]

        print( str( reservations ) )

        for reservation in reservations:
            instances = reservation[ 'Instances' ]

            for instance in instances:
                instances_to_start.append( instance[ 'InstanceId' ] )

        if instances_to_start:
            payload = {
                "region": regionName,
                "instances": instances_to_start
            }
            response[ 'body' ].append( payload )

            lambda_client = boto3.client( 'lambda' )
            lambda_client.invoke( 
                FunctionName=start_lambda_function,
                InvocationType='Event',
                LogType='None',
                Payload=json.dumps( payload )
            )

    return response