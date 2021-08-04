import * as ec2 from '@aws-cdk/aws-ec2';
import * as iam from '@aws-cdk/aws-iam';
import * as cdk from '@aws-cdk/core';
import { DnsProvider } from './dns-provider';

export interface CrossAccountVpc {
  /**
   * VPCs to associate the PHZ with
   */
  readonly vpc: ec2.IVpc;
  /**
   * An IAM role to assume to "switch" to the VPC account, to associate the PHZ with the VPC. If
   * not specified, CDK credentials will be used directly (that means, CDK must be authenticated
   * to the account where the VPC is)
   */
  readonly vpcAccountRole?: iam.IRole;
}

export interface CrossAccountHostedZoneProps {
  /**
   * The name of the domain
   */
  readonly zoneName: string;

  /**
   * Any comments that you want to include about the hosted zone
   */
  readonly comment?: string;

  /**
   * VPCs to associate the PHZ with, including the VPC account information (as the VPC can be in
   * a different account than the PHZ itself)
   */
  readonly vpcs: CrossAccountVpc[];

  /**
   * An IAM role to assume to create the private hosted zone. Use if the PHZ should be deployed
   * in different account than the CDK stack (default: CDK credentials are directly used)
   */
  readonly zoneAccountRole?: iam.IRole;
}

/**
 * Define a Route53 Private Hosted Zone, same as @aws-cdk/aws-route53.PrivateHostedZone, but allows
 * associating the PHZ with VPC(s) in different AWS accounts
 */
export class CrossAccountHostedZone extends cdk.Construct implements cdk.ITaggable {
  public readonly tags: cdk.TagManager;

  /** @internal */
  private readonly _props: CrossAccountHostedZoneProps;

  constructor(scope: cdk.Construct, id: string, props: CrossAccountHostedZoneProps) {
    super(scope, id);

    if (props.vpcs.length == 0) {
      throw new Error('A private hosted zone must be associated with at least one VPC');
    }

    this.tags = new cdk.TagManager(cdk.TagType.KEY_VALUE, 'CrossAccountHostedZone');
    this._props = props;
  }

  // postpone the actual CustomResource creation to prepare phase, so it has access to the rendered tags
  protected prepare() {
    const stack = cdk.Stack.of(this);
    const provider = DnsProvider.getOrCreate(this);

    // ensure the provider is authorized to assume all the needed roles
    provider.grantAssumeRoles([this._props.zoneAccountRole, ...this._props.vpcs.map(vpc => vpc.vpcAccountRole)].filter(x => x) as iam.IRole[]);

    new cdk.CustomResource(this, 'PrivateHostedZone', {
      serviceToken: provider.serviceToken,
      resourceType: 'Custom::CDK-DNS-CrossAccountPrivateHostedZone',
      properties: {
        zoneName: this._props.zoneName,
        comment: this._props.comment,
        vpcs: this._props.vpcs.map((cav) => {
          return {
            vpcId: cav.vpc.vpcId,
            vpcRegion: stack.region, // TODO: it might be desirable to support VPCs in multiple regions here
            role: cav.vpcAccountRole?.roleArn,
          };
        }),
        zoneAccountRole: this._props.zoneAccountRole?.roleArn,
        tags: this.tags.renderTags(),
      },
    });
  }
}