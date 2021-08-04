import time
import boto3
import logging


def aws_session(role=None):
    if role:
        creds = boto3.client('sts').assume_role(RoleArn=role, RoleSessionName='DnsPoc')['Credentials']
        return boto3.session.Session(aws_access_key_id=creds['AccessKeyId'],
                                     aws_secret_access_key=creds['SecretAccessKey'],
                                     aws_session_token=creds['SessionToken'])
    else:
        return boto3


class Zone(object):
    def __init__(self, zone_id=None, props=None, from_existing=None, logger=None):
        self.zone_id = zone_id
        self.domain_name = None
        self.comment = None
        self.tags = None
        self.zone_account_role = None
        self.same_account_vpcs = None
        self.cross_account_vpcs = None
        self._log = logger if logger else logging

        if props:
            self._load_properties(props)
        elif from_existing:
            self._load_existing(from_existing)

        self._zone_account = aws_session(self.zone_account_role)
        self.account_number = self._zone_account.client('sts').get_caller_identity().get('Account')
        self._temporary_vpc = None

    def _load_properties(self, props):
        self.domain_name = props['zoneName'].rstrip('.') + '.'  # ensure we always have the trailing dot
        self.comment = props.get('comment', '')
        self.tags = props.get('tags', [])
        self.zone_account_role = props.get('zoneAccountRole', None)
        self.same_account_vpcs = [(vpc['vpcId'], vpc['vpcRegion']) for vpc in props['vpcs'] if vpc.get('role', None) == self.zone_account_role]
        self.cross_account_vpcs = [vpc for vpc in props['vpcs'] if vpc.get('role') != self.zone_account_role]

        if not self.same_account_vpcs and not self.cross_account_vpcs:
            raise Exception('A private hosted zone must be associated with at least one VPC in the same or different account')

    def _load_existing(self, physical_id):
        pass

    def _create_temporary_vpc(self):
        tmp_vpc_name = f'_TEMP_PHZ_VPC_{time.time()}'
        self._log.info(f'Creating temporary VPC {tmp_vpc_name} in the child account')
        ec2 = self._zone_account.client('ec2')

        # The VPC will never be used or connected to any other network so the CIDR block here really doesn't matter
        vpc = ec2.create_vpc(CidrBlock='172.31.255.240/28',
                            TagSpecifications=[dict(ResourceType='vpc', Tags=[dict(Key='Name', Value=tmp_vpc_name)])])
        self._temporary_vpc = vpc['Vpc']['VpcId']
        
        self._log.info(f'Temporary VPC {tmp_vpc_name} created with VPC ID {self._temporary_vpc}')
        return self._temporary_vpc, ec2.meta.region_name

    def _delete_temporary_vpc(self):
        if self._temporary_vpc:
            self._log.info(f'Deleting temporary VPC {self._temporary_vpc}')
            ec2 = self._zone_account.client('ec2')
            ec2.delete_vpc(VpcId=self._temporary_vpc)
            self._temporary_vpc = None

    def _create_hosted_zone(self, vpc_id, vpc_region):
            self._log.info(f'Creating private hosted zone {self.domain_name}')
            route53 = self._zone_account.client('route53')
            zone = route53.create_hosted_zone(Name=self.domain_name,
                                            CallerReference=f'{self.domain_name}:{time.time()}',
                                            VPC=dict(VPCId=vpc_id, VPCRegion=vpc_region),
                                            HostedZoneConfig=dict(PrivateZone=True, Comment=self.comment))
            self.zone_id = zone['HostedZone']['Id']
            self._log.info(f'Hosted zone {self.domain_name} created with ID {self.zone_id}')

    def _apply_tags(self):
        if self.tags:
            self._log.info(f'Settings tags on the hosted zone {self.domain_name}')
            route53 = self._zone_account.client('route53')
            # TODO: add RemoveTags feature
            route53.change_tags_for_resource(ResourceType='hostedzone', ResourceId=self.zone_id, AddTags=self.tags)

    def _create_association_authorization(self, vpc, vpc_region):
        self._log.info(f'Creating association authorization for zone {self.domain_name} and VPC {vpc}')
        route53 = self._zone_account.client('route53')
        route53.create_vpc_association_authorization(HostedZoneId=self.zone_id, VPC=dict(VPCId=vpc, VPCRegion=vpc_region))

    def _delete_all_association_authorizations(self):
        route53 = self._zone_account.client('route53')
        vpcs = route53.list_vpc_association_authorizations(HostedZoneId=self.zone_id)['VPCs']
        for vpc in vpcs:
            route53.delete_vpc_association_authorization(HostedZoneId=self.zone_id, VPC=vpc)

    def _associate_vpc(self, session, vpc, vpc_region):
        self._log.info(f'Associating zone {self.domain_name} with VPC {vpc}')
        route53 = session.client('route53')
        route53.associate_vpc_with_hosted_zone(HostedZoneId=self.zone_id, VPC=dict(VPCId=vpc, VPCRegion=vpc_region))

    def _disassociate_vpc(self, session, vpc, vpc_region):
        self._log.info(f'Disassociating zone {self.domain_name} ({self.zone_id}) from VPC {vpc}')
        route53 = session.client('route53')
        route53.disassociate_vpc_from_hosted_zone(HostedZoneId=self.zone_id, VPC=dict(VPCId=vpc, VPCRegion=vpc_region))

    def _update_comment(self, comment):
        self._log.info(f'Updating comment for hosted zone {self.domain_name} ({self.zone_id})')
        route53 = self._zone_account.client('route53')
        route53.update_hosted_zone_comment(Id=self.zone_id, Comment=comment)
        self.comment = comment

    def already_exists(self):
        route53 = self._zone_account.client('route53')
        zones = route53.list_hosted_zones_by_name(DNSName=self.domain_name, MaxItems='1')['HostedZones']
        if len(zones) and zones[0]['Name'] == self.domain_name:
            return True
        return False

    def create(self):
        # Unfortunately, private hosted zone cannot be created without being associated with one VPC within the same
        # account - if user didn't specify any same-account VPCs to associate the PHZ with, we create a temporary VPC.
        # This will be deleted after the zone is successfully associated with another VPC in different account.
        if self.same_account_vpcs:
            zone_creation_vpc, zone_creation_vpc_region = self.same_account_vpcs[0]
        else:
            zone_creation_vpc, zone_creation_vpc_region = self._create_temporary_vpc()
            
        try:
            self._create_hosted_zone(zone_creation_vpc, zone_creation_vpc_region)

            self._apply_tags()

            # If there are more VPCs in the same account as the PHZ, associate them too
            for vpc_id, vpc_region in self.same_account_vpcs[1:]:
                self._associate_vpc(self._zone_account, vpc_id, vpc_region)

            # Associate the PHZ with the different account VPCs
            try:
                for cav in self.cross_account_vpcs:
                    vpc_account = aws_session(cav.get('role', None))
                    vpc, vpc_region = cav['vpcId'], cav['vpcRegion']
                    self._create_association_authorization(vpc=vpc, vpc_region=vpc_region)
                    self._associate_vpc(vpc_account, vpc, vpc_region)
            finally:
                self._delete_all_association_authorizations()

            if self._temporary_vpc:
                self._disassociate_vpc(self._zone_account, vpc=self._temporary_vpc, vpc_region=zone_creation_vpc_region)
        finally:
            self._delete_temporary_vpc()

    def update(self, new_props):
        desired = Zone(zone_id=self.zone_id, props=new_props, logger=self._log)

        # some parameters cannot be updated in-place, in such case, create a new zone
        if self.account_number != desired.account_number or self.domain_name != desired.domain_name:
            desired.create()
            return desired.zone_id

        if desired.comment != self.comment:
            self._update_comment(desired.comment)

        self.tags = desired.tags
        self._apply_tags()

        # Associate with additional VPCs in the same account
        same_account_vpcs_new = list(set(desired.same_account_vpcs) - set(self.same_account_vpcs))
        for vpc_id, vpc_region in same_account_vpcs_new:
            self._associate_vpc(self._zone_account, vpc_id, vpc_region)

        # Associate with additional cross-account VPCs
        old_ids = [vpc['vpcId'] for vpc in self.cross_account_vpcs]
        cross_account_vpcs_new = [vpc for vpc in desired.cross_account_vpcs if vpc['vpcId'] not in old_ids]
        try:
            for cav in cross_account_vpcs_new:
                vpc_account = aws_session(cav.get('role', None))
                vpc, vpc_region = cav['vpcId'], cav['vpcRegion']
                self._create_association_authorization(vpc=vpc, vpc_region=vpc_region)
                self._associate_vpc(vpc_account, vpc, vpc_region)
        finally:
            self._delete_all_association_authorizations()

        # Disassociate same account VPCs that are no longer desired
        same_account_vpcs_dis = list(set(self.same_account_vpcs) - set(desired.same_account_vpcs))
        for vpc_id, vpc_region in same_account_vpcs_new:
            self._disassociate_vpc(self._zone_account, vpc_id, vpc_region)

        # Disassociate cross-account VPCs that are no longer desired
        new_ids = [vpc['vpcId'] for vpc in desired.cross_account_vpcs]
        cross_account_vpcs_dis = [vpc for vpc in self.cross_account_vpcs if vpc['vpcId'] not in new_ids]
        for cav in cross_account_vpcs_dis:
            vpc_account = aws_session(cav.get('role', None))
            vpc, vpc_region = cav['vpcId'], cav['vpcRegion']
            self._disassociate_vpc(vpc_account, vpc, vpc_region)
       
        return self.zone_id
    
    def delete(self):
        self._log.info(f'Deleting private hosted zone {self.domain_name} ({self.zone_id})')
        route53 = self._zone_account.client('route53')
        route53.delete_hosted_zone(Id=self.zone_id)


#def is_associated(session, vpc, zone):
#    route53 = session.client('route53')
#
#    def associated_zones():
#        page_params = {}
#        while page_params is not None:
#            resp = route53.list_hosted_zones_by_vpc(VPCId=vpc, VPCRegion=route53.meta.region_name, **page_params)
#            for z in resp['HostedZoneSummaries']:
#                yield z['HostedZoneId']
#            page_params = resp.get('NextToken', None)
#
#    for z in associated_zones():
#        if z == zone:
#            print(f'Zone is already associated with VPC {vpc}')
#            return True
#
#    return False
#
#
#def read_hosted_zone(session, zone_id):
#    route53 = session.client('route53')
#    zone = route53.get_hosted_zone(Id=zone_id)['HostedZone']
#    return zone['Name'], zone['Config'].get('Comment', None), zone['VPCs']
#
#
#def read_hosted_zone_tags(session, zone_id):
#    route53 = session.client('route53')
#    return route53.list_tags_for_resource(ResourceType='hostedzone', ResourceId=zone_id)['ResourceTagSet']['Tags']