import logging
from zone import Zone

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)
LOG.setLevel(level=logging.INFO)
     

def handler(event, context):
    LOG.info(event)
    request_type = event['RequestType']

    if request_type == 'Create':
        return on_create(event)
    elif request_type == 'Update':
        return on_update(event)
    elif request_type == 'Delete':
        return on_delete(event)
    else:
        raise Exception(f'Invalid request type "{request_type}"')


def on_create(event):
    props = event['ResourceProperties']

    zone = Zone(props=props, logger=LOG)

    LOG.info(f'CREATE HANDLER - domain: {zone.domain_name}')

    if zone.already_exists():
        raise Exception(f'Private hosted zone with zone name {zone.domain_name} already exists in account {zone.account_number}')

    zone.create()

    return {'PhysicalResourceId': zone.zone_id}


def on_update(event):
    zone_id = event['PhysicalResourceId']
    old_props = event['OldResourceProperties']
    new_props = event['ResourceProperties']

    zone = Zone(zone_id=zone_id, props=old_props, logger=LOG)
    LOG.info(f'UPDATE HANDLER - domain: {zone.domain_name}')

    # If a property was changed that Route53 won't allow to update in-place a new PHZ will be created
    # and zone_id updated accordingly. The old zone is not deleted here - that should be handled by CloudFormation:
    # If it detects the physical ID has changed, it should invoke delete handler with the old physical ID
    zone_id = zone.update(new_props)

    return {'PhysicalResourceId': zone_id}
    

def on_delete(event):
    zone_id = event['PhysicalResourceId']
    props = event['ResourceProperties']

    zone = Zone(zone_id=zone_id, props=props, logger=LOG)

    LOG.info(f'DELETE HANDLER - hosted zone {zone.domain_name} ({zone})')

    zone.delete()