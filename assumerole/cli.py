""" this is the cli portion of of assumerole tool """
# @author Dan Sikes <dan.sikes@pearson.com>
# @date  10/11/18

import argparse
from .FileParser import FileParser

class MFATokenValidator(argparse.Action):

    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @staticmethod
    def validate(parser, value):
        value = int(value)
        if not isinstance(value, int):
            parser.error('{} is not a valid mfa token'.format(value))
        
        if len(str(value)) != 6:
            parser.error('{} must be 6 digits.'.format(value))


class DurationValidator(argparse.Action):
    
    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @staticmethod
    def validate(parser, value):
        if int(value) > 43200:
            parser.error('{} exceeds max limit of 43200 seconds.'.format(value))


# written as a function to allow easier testing
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cred',       '-c', required=True, help='name of credential section located in ~/.aws/credentials')
    parser.add_argument('--profile',    '-p', required=True, help='name of config profile located in ~/.aws/config')
    parser.add_argument('--duration',   '-d', default=3600,  help='duration for new session (in seconds)')
    parser.add_argument('--token',      '-t', default=None,  help='mfa token to validate session')

    return parser

# used by entrypoint in setup.py to provide CLI functionality.
def main():
    try:
        parser = create_parser()
        args = parser.parse_args()
        if args.token is None:
            args.token = input('Enter MFA Token: ')
            MFATokenValidator.validate(parser, args.token)
        if args.duration is not None:
            DurationValidator.validate(parser, args.duration)

        fp = FileParser(args)
        fp.assume()
    except KeyboardInterrupt:
        print("\nExiting due to user action...")
    except Exception as err:
        print("ERROR: %s" % (str(err)))
