# AWS Assume Role Helper Tool
Easily switch between AWS IAM roles.

## Setup
Put this in your .bash_profile or .bashrc

```
function awscreds() {
    eval $(assumerole $@)
}
```

Then create any aliases you may need:

` alias assumenonprod='awscreds assume <credentialSectionName> <configProfileSectionName> <DurationInSeconds>' `

## Usage

`assumenonprod <MFAToken>`

## Other Commands

You can view available commands by simply running `awscreds`

So far we support:
- assume
- list
- load
- clean
- remove
