# import sys
# import unittest
# import configparser
# import time
# from assumerole import FileParser

# class Namespace:
#     def __init__(self, **kwargs):
#         self.__dict__.update(kwargs)

# args = Namespace()
# ####################################################################################
# # You must set these according to the environment you are testing...
# args.cred = 'cred1'
# args.profile = 'profile content-non-prod'
# args.duration = 3600
# args.token = input('Enter MFA token: ')
# ####################################################################################
# args.session = None # scoped to allow for 1 time MFA to pass...

# class FileParserTestCase(unittest.TestCase):
#     """Tests for `FileParser.py`."""

#     def test_step1_config_parsers(self):
#         fp = FileParser(args)
#         fp._parse_files()
#         assert isinstance(fp.config, configparser.ConfigParser)
#         assert isinstance(fp.creds, configparser.ConfigParser)

#     def test_step2_required_options_get_set(self):
#         fp = FileParser(args)
#         fp._get_all_required_options_from_selected_profile()
#         assert fp.args.role_session_name is not None
#         assert fp.args.mfa_serial is not None
#         assert fp.args.role_arn is not None
    
#     # TODO: look into using moto for possibly mocking the STS calls.
#     def test_step3_session_is_generated(self):
#         fp = FileParser(args)
#         fp._get_all_required_options_from_selected_profile()
#         args.session = fp.get_new_session() # to prevent error for 1 time MFA token
#         assert args.session is not None
    
#     def test_step4_default_is_written_to_config_file(self):
#         fp = FileParser(args)
#         fp._get_all_required_options_from_selected_profile()
#         fp.session = args.session
#         fp._set_template_section()

#         with open(fp.awsconfig, 'r') as configfile:
#             config = configfile.read()
        
#         assert '[__replace__]' in config

#         fp._set_default_section()
        
#         with open(fp.awsconfig, 'r') as configfile:
#             config = configfile.read()

#         assert '[default]' in config
#         assert '[__replace__]' not in config

# if __name__ == '__main__':
#     unittest.main(verbosity=2)