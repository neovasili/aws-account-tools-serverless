import json
import boto3
import os
import datetime
import pytz

STAGE = os.environ[ 'stage' ]
STOP_INSTANCES_FUNCTION_NAME = os.environ[ 'stop_instances_function_name' ]
START_INSTANCES_FUNCTION_NAME = os.environ[ 'start_instances_function_name' ]
DEFAULT_REGION = os.environ[ 'default_region' ]
DEFAULT_TIMEZONE = os.environ[ 'default_timezone' ]

class EC2OperationClient( object ):
    def __init__( self, region, operation ):
        self.__region = region
        self.__operation = operation
        self.__ec2_client = boto3.client( 'ec2', region_name=region )
    
    def operate_instances( self ):
        payload = None

        instances_to_operate = self.get_filtered_instances_for_region()

        if instances_to_operate:
            payload = {
                "operation": self.__operation,
                "region": self.__region,
                "instances": instances_to_operate
            }

            LambdaStartStopInstancesInvocationClient( payload ).send_instances_to_lambda_function()

        return payload
    
    def get_filtered_instances_for_region( self ):
        filtered_instances = []
        filters = EC2OperationInstancesFilter( self.__operation ).create_instances_operation_filter()

        reservations = self.__ec2_client.describe_instances( Filters=filters )[ 'Reservations' ]

        for reservation in reservations:
            instances = reservation[ 'Instances' ]

            for instance in instances:
                filtered_instances.append( instance[ 'InstanceId' ] )

        return filtered_instances

class StartEC2InstancesClient( EC2OperationClient ):
    def __init__( self, region ):
        self.__operation = 'start'
        EC2OperationClient.__init__( self, region, self.__operation )

class StopEC2InstancesClient( EC2OperationClient ):
    def __init__( self, region ):
        self.__operation = 'stop'
        EC2OperationClient.__init__( self, region, self.__operation )

class EC2OperationInstancesFilter( object ):
    def __init__( self, operation ):
        self.__operation = operation

    def create_instances_operation_filter( self ):
        timezone = 'Europe/Madrid'

        instance_state_match = {
            "start": "stopped",
            "stop": "running"
        } 

        if DEFAULT_TIMEZONE:
            timezone = DEFAULT_TIMEZONE

        timezone_instance = pytz.timezone( timezone )
        now = datetime.datetime.now().astimezone( timezone_instance )

        currentHour = now.hour
        currentDayOfWeek = now.weekday()
        weekday_dict = [ 'monday', 
            'tuesday', 
            'wednesday', 
            'thursday', 
            'friday', 
            'saturday', 
            'sunday' ] 

        filters = [ 
            {
                'Name':'tag:' + self.__operation + '-' + weekday_dict[ currentDayOfWeek ], 'Values':[ str( currentHour ) ]
            },
            {
                'Name':'tag:stage', 'Values':[ STAGE ]
            },
            {
                'Name':'instance-state-name', 'Values':[ instance_state_match[ self.__operation ] ]
            } 
        ]

        return filters

class LambdaStartStopInstancesInvocationClient( object ):
    def __init__( self, payload ):
        self.__payload = payload

    def send_instances_to_lambda_function( self ):
        lambda_function_name = {
            "start": START_INSTANCES_FUNCTION_NAME,
            "stop": STOP_INSTANCES_FUNCTION_NAME
        }

        lambda_client = boto3.client( 'lambda' )
        lambda_client.invoke( 
            FunctionName=lambda_function_name[ self.__payload[ 'operation' ] ],
            InvocationType='Event',
            LogType='None',
            Payload=json.dumps( self.__payload )
        )


def handler( event, context ):
    response = {
        "statusCode": 200,
        "body": []
    }

    if DEFAULT_REGION:
        result = StartEC2InstancesClient( DEFAULT_REGION ).operate_instances()
        if result: response[ 'body' ].append( result )
        result = StopEC2InstancesClient( DEFAULT_REGION ).operate_instances()
        if result: response[ 'body' ].append( result )

    else:
        ec2 = boto3.client( 'ec2' )
        regions = ec2.describe_regions()
        
        for region in regions[ 'Regions' ]:
            region_name = region[ 'RegionName' ]

            result = StartEC2InstancesClient( region_name ).operate_instances()
            if result: response[ 'body' ].append( result )
            result = StopEC2InstancesClient( region_name ).operate_instances()
            if result: response[ 'body' ].append( result )

    return response