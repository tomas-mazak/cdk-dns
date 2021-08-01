const { AwsCdkConstructLibrary } = require('projen');
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
  repositoryUrl: 'https://github.com/tomas/cdk-dns.git',

  // cdkDependencies: undefined,        /* Which AWS CDK modules (those that start with "@aws-cdk/") does this library require when consumed? */
  // cdkTestDependencies: undefined,    /* AWS CDK modules required for testing. */
  // deps: [],                          /* Runtime dependencies of this module. */
  // devDeps: [],                       /* Build dependencies for this module. */
  // packageName: undefined,            /* The "name" in package.json. */
  // projectType: ProjectType.UNKNOWN,  /* Which type of project this is (library/app). */
  // release: undefined,                /* Add release management to this project. */
});
project.synth();