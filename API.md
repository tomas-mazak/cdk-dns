# API Reference <a name="API Reference"></a>

## Constructs <a name="Constructs"></a>

### CrossAccountHostedZone <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone"></a>

- *Implements:* [`@aws-cdk/core.ITaggable`](#@aws-cdk/core.ITaggable)

Define a Route53 Private Hosted Zone, same as @aws-cdk/aws-route53.PrivateHostedZone, but allows associating the PHZ with VPC(s) in different AWS accounts.

#### Initializer <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone.Initializer"></a>

```typescript
import { CrossAccountHostedZone } from '@tomas-mazak/cdk-dns'

new CrossAccountHostedZone(scope: Construct, id: string, props: CrossAccountHostedZoneProps)
```

##### `scope`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone.parameter.scope"></a>

- *Type:* [`@aws-cdk/core.Construct`](#@aws-cdk/core.Construct)

---

##### `id`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone.parameter.id"></a>

- *Type:* `string`

---

##### `props`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone.parameter.props"></a>

- *Type:* [`@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps`](#@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps)

---



#### Properties <a name="Properties"></a>

##### `tags`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZone.property.tags"></a>

- *Type:* [`@aws-cdk/core.TagManager`](#@aws-cdk/core.TagManager)

TagManager to set, remove and format tags.

---


## Structs <a name="Structs"></a>

### CrossAccountHostedZoneProps <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps"></a>

#### Initializer <a name="[object Object].Initializer"></a>

```typescript
import { CrossAccountHostedZoneProps } from '@tomas-mazak/cdk-dns'

const crossAccountHostedZoneProps: CrossAccountHostedZoneProps = { ... }
```

##### `vpcs`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps.property.vpcs"></a>

- *Type:* [`@tomas-mazak/cdk-dns.CrossAccountVpc`](#@tomas-mazak/cdk-dns.CrossAccountVpc)[]

VPCs to associate the PHZ with, including the VPC account information (as the VPC can be in a different account than the PHZ itself).

---

##### `zoneName`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps.property.zoneName"></a>

- *Type:* `string`

The name of the domain.

---

##### `comment`<sup>Optional</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps.property.comment"></a>

- *Type:* `string`

Any comments that you want to include about the hosted zone.

---

##### `zoneAccountRole`<sup>Optional</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountHostedZoneProps.property.zoneAccountRole"></a>

- *Type:* [`@aws-cdk/aws-iam.IRole`](#@aws-cdk/aws-iam.IRole)

An IAM role to assume to create the private hosted zone.

Use if the PHZ should be deployed
in different account than the CDK stack (default: CDK credentials are directly used)

---

### CrossAccountVpc <a name="@tomas-mazak/cdk-dns.CrossAccountVpc"></a>

#### Initializer <a name="[object Object].Initializer"></a>

```typescript
import { CrossAccountVpc } from '@tomas-mazak/cdk-dns'

const crossAccountVpc: CrossAccountVpc = { ... }
```

##### `vpc`<sup>Required</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountVpc.property.vpc"></a>

- *Type:* [`@aws-cdk/aws-ec2.IVpc`](#@aws-cdk/aws-ec2.IVpc)

VPCs to associate the PHZ with.

---

##### `vpcAccountRole`<sup>Optional</sup> <a name="@tomas-mazak/cdk-dns.CrossAccountVpc.property.vpcAccountRole"></a>

- *Type:* [`@aws-cdk/aws-iam.IRole`](#@aws-cdk/aws-iam.IRole)

An IAM role to assume to "switch" to the VPC account, to associate the PHZ with the VPC.

If
not specified, CDK credentials will be used directly (that means, CDK must be authenticated
to the account where the VPC is)

---



