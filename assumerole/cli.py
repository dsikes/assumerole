""" this is the cli portion of of assumerole tool """
# @author Dan Sikes <dan.sikes@pearson.com>
# @date  10/11/18

import sys
import argparse
from argparse import ArgumentParser, RawTextHelpFormatter
from .AWSCreds import AWSCreds


class MFATokenValidator(argparse.Action):

    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @staticmethod
    def validate(parser, value):
        
        if len(value) != 6:
            parser.error('{} must be 6 digits.'.format(value))

        value = int(value)
        if not isinstance(value, int):
            parser.error('{} is not a valid mfa token'.format(value))


class DurationValidator(argparse.Action):
    
    def __call__(self, parser, namespace, value, option_string=None):
        self.validate(parser, value)
        setattr(namespace, self.dest, value)

    @staticmethod
    def validate(parser, value):
        if int(value) > 43200:
            parser.error('{} exceeds max limit of 43200 seconds.'.format(value))


class MyParser(ArgumentParser):    

    # override method to use stderr instead of stdout
    def print_help(self, file=sys.stderr):
        self._print_message(self.format_help(), file)
         
    def error(self, message):
        print("ERROR: %s" % (str(message)), file=sys.stderr)
        sys.exit(2)

# written as a function to allow easier testing
def create_parser():
    parser = MyParser()
    subparsers = parser.add_subparsers(help='available commands')

    assume_command  = subparsers.add_parser("assume")
    list_command    = subparsers.add_parser("list")
    load_command    = subparsers.add_parser("load")
    clean_command   = subparsers.add_parser("clean")
    remove_command  = subparsers.add_parser("remove")    

    assume_command.add_argument('credential', help='name of credential section located in ~/.aws/credentials')
    assume_command.add_argument('profile', help='name of config profile located in ~/.aws/config')
    assume_command.add_argument('duration', help='duration for new session in seconds. (Defaults to 1hr)')
    assume_command.add_argument('token', default=None, help='mfa token to validate session')
    
    load_command.add_argument('access_key_id', help='Access Key ID of the role you want to load.')
    remove_command.add_argument('access_key_id', help='Access Key ID of the role you want to remove.')

    return parser

# used by entrypoint in setup.py to provide CLI functionality.
def main():
    
    try:
        parser = create_parser()
    
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
    
        command = sys.argv[1]
        args = parser.parse_args()
        cred = AWSCreds(args)

        if command == 'assume':
            DurationValidator.validate(parser, args.duration)
            MFATokenValidator.validate(parser, args.token)
            cred.assume()
    
        if command == 'list':
            cred.print_table()

        if command == 'load':
            cred.load_by_access_key_id(args.access_key_id)
        
        if command == 'clean':
            cred.clean_expired()

        if command == 'remove':
            cred.remove_by_access_key_id(args.access_key_id)
    
    except KeyboardInterrupt:
        print("\nExiting due to user action...", file=sys.stderr)
    except Exception as err:
        print("ERROR: %s" % (str(err)), file=sys.stderr)
