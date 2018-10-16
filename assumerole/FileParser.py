import os
import boto3
import configparser


class FileParser:
    """ this class manages manipulating the AWS config file and credentials file """
 
    def __init__(self, args):
        self.args = args
        
        self.homedir = os.path.expanduser('~')
        self.awsconfig = '%s/.aws/config' % self.homedir
        self.awscreds = '%s/.aws/credentials' % self.homedir

        if not os.path.isfile(self.awsconfig):
            raise Exception("ERROR: Unable to locate AWS config file!")
        
        if not os.path.isfile(self.awscreds):
            raise Exception("ERROR: Unable to locate AWS credentials file!")
        
    def _parse_files(self):
        self.creds = configparser.ConfigParser()
        self.creds.read([self.awscreds])
        
        self.config = configparser.ConfigParser()
        self.config.read([self.awsconfig])
    
    def _get_all_required_options_from_selected_profile(self):
        self._parse_files()
        self.args.role_session_name = self.config.get(self.args.profile, 'role_session_name')
        self.args.mfa_serial = self.config.get(self.args.profile, 'mfa_serial')
        self.args.role_arn =  self.config.get(self.args.profile, 'role_arn')
    
    def _remove_default_section(self):
        if 'default' in self.config.sections():
            self.config.remove_section('default')
        
        with open(self.awsconfig, 'w+') as configfile:
            self.config.write(configfile)

    def _set_default_section(self):
        self._remove_default_section()

        with open(self.awsconfig) as f:
            # have to add this due to the way config parser seems to work.. :( it doesn't allow adding "default" as a section... boo..
            update = f.read().replace('[__replace__]', '[default]')
        
        with open(self.awsconfig, "w") as f:
            f.write(update)
    
    def _set_template_section(self):
        if '__replace__' in self.config.sections():
            self.config.remove_section('__replace__')

        self.config.add_section('__replace__')
        self.config.set('__replace__', 'aws_access_key_id', self.session['Credentials']['AccessKeyId'])
        self.config.set('__replace__', 'aws_secret_access_key', self.session['Credentials']['SecretAccessKey'])
        self.config.set('__replace__', 'aws_session_token', self.session['Credentials']['SessionToken'])

        with open(self.awsconfig, 'w+') as configfile:
            self.config.write(configfile)
    
    def get_new_session(self):
        session = boto3.Session(profile_name=self.args.cred)
        client = session.client('sts')
        response = client.assume_role(
            RoleArn=self.args.role_arn,
            RoleSessionName=self.args.role_session_name,
            DurationSeconds=self.args.duration,
            SerialNumber=self.args.mfa_serial,
            TokenCode=str(self.args.token)
        )
        
        return response

    def assume(self):
        self._get_all_required_options_from_selected_profile()
        self.session = self.get_new_session()
        self._set_template_section()
        self._set_default_section()
        print("Assuming Role %s as %s" % (self.args.role_arn, self.args.role_session_name))
