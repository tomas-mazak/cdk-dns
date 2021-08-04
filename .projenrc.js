const { AwsCdkConstructLibrary, NodePackageManager } = require('projen');
const project = new AwsCdkConstructLibrary({
  author: 'Tomas Mazak',
  authorAddress: 'tomas@valec.net',
  authorName: 'Tomas Mazak',
  cdkVersion: '1.95.2',
  defaultReleaseBranch: 'main',
  description: 'High level constructs to setup DNS infrastructure for larger enterprises with multiple accounts and hybrid setup',
  devContainer: true,
  homepage: 'https://github.com/tomas-mazak/cdk-dns',
  name: 'cdk-dns',
  repositoryUrl: 'https://github.com/tomas-mazak/cdk-dns.git',

  packageManager: NodePackageManager.NPM,
  packageName: '@tomas-mazak/cdk-dns',

  cdkDependencies: [
    '@aws-cdk/core',
    '@aws-cdk/custom-resources',
    '@aws-cdk/aws-lambda',
    '@aws-cdk/aws-ec2',
    '@aws-cdk/aws-iam',
  ],
  // cdkTestDependencies: undefined,    /* AWS CDK modules required for testing. */
  // deps: [],                          /* Runtime dependencies of this module. */
  // devDeps: [],                       /* Build dependencies for this module. */
  // projectType: ProjectType.UNKNOWN,  /* Which type of project this is (library/app). */
  // release: undefined,                /* Add release management to this project. */
});
project.synth();
