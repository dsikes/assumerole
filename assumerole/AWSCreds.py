import os
import sys
import boto3
import configparser
import json
import hashlib
from datetime import date, datetime, timezone
import dateutil.parser
from tabulate import tabulate

class AWSCreds:
    """ this class manages manipulating the AWS config file and credentials file """
 
    def __init__(self, args):
        self.args = args
        self.homedir = os.path.expanduser('~')
        self.awsconfig = '%s/.aws/config' % self.homedir
        self.awscreds = '%s/.aws/credentials' % self.homedir
        self.cache_dir = '%s/.aws/cli/cache' % self.homedir
        self.utc_time = datetime.now(timezone.utc)
        self.creds  = []

        if not os.path.isfile(self.awsconfig):
            raise Exception("ERROR: Unable to locate AWS config file!")
        
        if not os.path.isfile(self.awscreds):
            raise Exception("ERROR: Unable to locate AWS credentials file!")
        
    def _parse_files(self):
        self.credentials = configparser.ConfigParser()
        self.credentials.read([self.awscreds])
        
        self.config = configparser.ConfigParser()
        self.config.read([self.awsconfig])
    
    def _get_all_required_options_from_selected_profile(self):
        self._parse_files()
        self.args.role_session_name = self.config.get(self.args.profile, 'role_session_name')
        self.args.mfa_serial = self.config.get(self.args.profile, 'mfa_serial')
        self.args.role_arn =  self.config.get(self.args.profile, 'role_arn')
    
    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    def _cache_creds(self, creds):
        json_output = json.dumps(creds, indent=4, sort_keys=True, default=self._json_serial)
        cache_filename = "{}/{}.json".format(self.cache_dir, hashlib.sha1(json_output.encode('latin-1')).hexdigest())

        with open(cache_filename, "w+") as text_file:
            text_file.write(json_output)
    
    def _get_role_details(self, cred):
        rolearn = cred.get("AssumedRoleUser", {}).get('Arn')
        account = rolearn.split(':')[4]
        suffix = rolearn.split(':')[5]
        rolename = suffix.split('/')[1:-1][0]
        return [account, rolename]
    
    def _valid_in_mins(self, cred):
        cred_time_str = cred.get('Credentials', {}).get('Expiration')
        cred_time = dateutil.parser.parse(cred_time_str)
        td = (cred_time - self.utc_time)
        minutes = (td.days*60*24) + (td.seconds // 60)
        if minutes < 0:
            return 'EXPIRED'
        return minutes

    def _load_cached_creds(self):
        self.creds = []
        cached_creds = [f for f in os.listdir(self.cache_dir) if os.path.isfile(os.path.join(self.cache_dir, f))]
        for cred in cached_creds:
            with open("{}/{}".format(self.cache_dir, cred)) as f:
                data = json.load(f)
                account, rolename = self._get_role_details(data)
                item = {
                    'AccessKeyId': data.get('Credentials', {}).get('AccessKeyId', ''),
                    'Age': self._valid_in_mins(data),
                    'Role': rolename,
                    'Account': account,
                    'FileName': cred
                }
                self.creds.append(item)
    
    
    def _get_cred_by_access_key_id(self, access_key_id):
        self._load_cached_creds()
        for cred in self.creds:
            if cred['AccessKeyId'] == access_key_id:
                return cred
        return False
    
    def _print_exported(self, cred):
        access_key_id = cred.get('Credentials', {}).get('AccessKeyId', '')
        secret_access_key = cred.get('Credentials', {}).get('SecretAccessKey', '')
        session_token = cred.get('Credentials', {}).get('SessionToken', '')
        print("""
export AWS_ACCESS_KEY_ID={access_key_id}
export AWS_SECRET_ACCESS_KEY={secret_access_key}
export AWS_SESSION_TOKEN={session_token}
""".format(access_key_id=access_key_id,
                   secret_access_key=secret_access_key,
                   session_token=session_token))
        role = cred.get('AssumedRoleUser', {}).get('Arn', '').split('/')[1]
        acct = cred.get('AssumedRoleUser', {}).get('Arn', '').split('/')[2]
        print("assuming role %s for %s" % (role, acct), file=sys.stderr)
    
    def clean_expired(self):
        self._load_cached_creds()
        removed = 0
        for cred in self.creds:
            if cred['Age'] == 'EXPIRED':
                os.remove("{}/{}".format(self.cache_dir, cred['FileName']))
                removed += 1
                # not sure if we need to add a print line for every removal.. its here if we do.
                # print("removed %s" % (cred['AccessKeyId']), file=sys.stderr)
        if removed == 0:
            print("no creds are expired!", file=sys.stderr)
        else:
            print("removed %s expired creds" % (removed), file=sys.stderr)

    def remove_by_access_key_id(self, access_key_id):
        cred = self._get_cred_by_access_key_id(access_key_id)
        if cred:
            os.remove("{}/{}".format(self.cache_dir, cred['FileName']))
            print("removed %s!" % (access_key_id), file=sys.stderr)
            return
        print("invalid access key id: %s" % (access_key_id), file=sys.stderr)
    

    def load_by_access_key_id(self, access_key_id):
        cred = self._get_cred_by_access_key_id(access_key_id)
        if cred:
            with open("{}/{}".format(self.cache_dir, cred['FileName'])) as f:
                data = json.load(f)
                self._print_exported(data)
                return
        print("invalid access key id: %s" % (access_key_id), file=sys.stderr)

    def print_table(self):
        self._load_cached_creds()
        results = []
        headers=['Role', 'Account', 'Age', 'AccessKeyId']
        for lp, i in enumerate(self.creds):
            row = []
            for h in headers:
                row.append(i.get(h, ''))
            results.append(row)

        print(tabulate(results, headers=headers), file=sys.stderr)
    
    
    def get_new_credentials(self):
        self._get_all_required_options_from_selected_profile()
        session = boto3.Session(profile_name=self.args.credential)
        client = session.client('sts')
        response = client.assume_role(
            RoleArn=self.args.role_arn,
            RoleSessionName=self.args.role_session_name,
            DurationSeconds=int(self.args.duration),
            SerialNumber=self.args.mfa_serial,
            TokenCode=str(self.args.token)
        )
        
        return response

    def assume(self):
        creds = self.get_new_credentials()
        self._cache_creds(creds)
        self._print_exported(creds)
        
