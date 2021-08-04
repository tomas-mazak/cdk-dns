import * as path from 'path';
import * as iam from '@aws-cdk/aws-iam';
import * as lambda from '@aws-cdk/aws-lambda';
import * as cdk from '@aws-cdk/core';
import * as cr from '@aws-cdk/custom-resources';

export interface DnsProviderProps extends cdk.NestedStackProps {}

export class DnsProvider extends cdk.NestedStack {
  /**
   * Return a signleton instance of DnsProvider (one per stack)
   *
   * @param scope Parent construct used to identify the correct stack
   */
  public static getOrCreate(scope: cdk.Construct) {
    const stack = cdk.Stack.of(scope);
    let provider = stack.node.tryFindChild('DnsProvider') as DnsProvider;
    if (!provider) {
      provider = new DnsProvider(stack, 'DnsProvider', {});
    }
    return provider;
  }

  public readonly serviceToken: string;

  /** @internal */
  private readonly _role: iam.IRole;

  public constructor(scope: cdk.Construct, id: string, props: DnsProviderProps) {
    super(scope, id, props);

    const onEventHandler = new lambda.Function(this, 'Handler', {
      runtime: lambda.Runtime.PYTHON_3_8,
      code: lambda.Code.fromAsset(path.join(__dirname, '..', 'lambda', 'dnsprovider')),
      handler: 'index.handler',
      timeout: cdk.Duration.minutes(15),
    });

    const provider = new cr.Provider(this, 'Provider', {
      onEventHandler,
    });

    this.serviceToken = provider.serviceToken;
    this._role = onEventHandler.role!;

    // FIXME: reduce the permissions to only the actions that are really needed
    this._role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonRoute53FullAccess'));
    this._role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonVPCFullAccess'));
  }

  public grantAssumeRoles(roles: iam.IRole[]) {
    for (let role of roles) {
      role.grant(this._role, 'sts:AssumeRole');
    }
  }
}