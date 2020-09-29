#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chrome Browser Cloud Management (CBCM) command line tool."""

import argparse
import http
import json
import os.path
import sys

import google.auth.transport.requests
from google.oauth2.service_account import Credentials

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry # pylint: disable=E0401
from requests_toolbelt import sessions

__version__ = '0.2'
__author__ = 'Jay Lee'

SCOPES = ['https://www.googleapis.com/auth/admin.directory.device.chromebrowsers']

def get_args(args):
    """Parse command line arguments."""

    parser = argparse.ArgumentParser('Break19')
    parser.add_argument('--credentials-file', dest='credentials_file',
                        required=True,
                        help='location of your service account credentials')
    parser.add_argument('--customer', dest='customer', default='my_customer',
                        help='Customer ID from admin.google.com > ' \
                                        'Account > Account settings > Profile.')
    parser.add_argument('--admin', dest='admin', required=True,
                        help='Email address of admin user to act as.')
    parser.add_argument('--debug', action='store_true',
                        help='Show HTTP session details')
    parser.add_argument('--version', action='version', version=__version__)

    subparsers = parser.add_subparsers()

    arguments = {
        'list-browsers': [
            (['--orgunit'], {'dest': 'orgunit', 'help': 'OrgUnit to scope results'}),
            (['--orderby'], {'help': 'Sort results by property'}),
            (['--projection'], {'default': 'BASIC',
             'choices': ['BASIC', 'FULL'],
             'help': 'retrieve basic or full browser details'}),
            (['--query'], {'help': 'Query to scope results'}),
            (['--sortorder'], {'default': 'ASCENDING',
             'choices': ['ASCENDING', 'DESCENDING'], 'help': 'Sort order'}),
            (['--fields'],
             {'help': 'Limit fields retrieved and output.'}),
         ],
         'update-browser': [
             (['--id'], {'required': True,
              'help': 'deviceId of the browser to update'}),
             (['--user'], {'help': 'user of the browser'}),
             (['--location'], {'help': 'location of the browser'}),
             (['--notes'], {'help': 'notes of the browser'}),
             (['--assetid'], {'help': 'asset tag id of the browser'}),
             (['--fields'],
              {'help': 'Limit fields retrieved and output.'}),
         ],
         'delete-browser': [
             (['--id'], {'required': True,
              'help': 'deviceId of the browser to delete'}),
         ],
         'move-browsers': [
             (['--ids'],
              {'help': 'comma-seperated deviceIds of the browsers to move'}),
             (['--orgunit'], {'required': True,
              'help': 'Org Unit location to move browsers'}),
             (['--query'], {'help': 'Query to scope devices to be moved.'}),
             (['--file-of-ids'],
              {'dest': 'file_of_ids',
               'help': 'File containing deviceIds of the browser to move, ' \
                'one per line'})
         ],
         'list-tokens': [
             (['--orgunit'], {'help': 'OrgUnit to scope results'}),
             (['--query'], {'help': 'Query to scope results'}),
             (['--fields'], {'help': 'Limit fields retrieved and output'}),
         ],
         'create-token': [
             (['--expire'], {'help': 'Optional expiration time of the ' \
               'enrollment token in "yyyy-MM-ddThh:mm:ssZ" format.'}),
             (['--orgunit'], {'help': 'The organization unit to create an ' \
               'enrollment token for. If this' \
                                       'field is not specified, the ' \
                                       'enrollment token is created for the ' \
                                       'root organization unit.'}),
             (['--ttl'], {'help': 'Life of the created enrollment token'}),
             (['--fields'], {'help': 'Limit fields retrieved and output'}),
         ],
         'revoke-token': [
             (['--id'], {'required': True,
              'help': 'permanent ID of the token to revoke'}),
         ],
    }

    for argument, flags in arguments.items():
        argument_p = subparsers.add_parser(argument)
        for args1, args2 in flags:
            argument_p.add_argument(*args1, **args2)
        myfunc = globals()[argument.replace('-', '')]
        argument_p.set_defaults(func=myfunc)

    return parser.parse_args(args)


def listbrowsers(args, httpc):
    """List browsers."""
    params = {}
    if args.orderby:
        params['orderBy'] = args.orderby
    if args.orgunit:
        params['orgUnitPath'] = args.orgunit
    if args.projection:
        params['projection'] = args.projection
    if args.query:
        params['query'] = args.query
    if args.sortorder:
        params['sortOrder'] = args.sortorder
    if args.fields:
        params['fields'] = args.fields
    browsers = []
    while True:
        result = httpc.get('devices/chromebrowsers', params=params)
        browsers += result.json().get('browsers', [])
        if 'nextPageToken' in result:
            params['pageToken'] = result['nextPageToken']
        else:
            break
    print_json(browsers)

def getbrowser(args, httpc):
    """List browsers."""
    params = {}
    if args.fields:
        params['fields'] = args.fields
    result = httpc.get(f'devices/chromebrowsers/{args.id}', params=params)
    print_json(result.json())


def updatebrowser(args, httpc):
    """Update browser."""
    body = {'deviceId': args.id}
    params = {}
    if args.user:
        body['annotatedUser'] = args.user
    if args.location:
        body['annotatedLocation'] = args.location
    if args.notes:
        body['annotatedNotes'] = args.notes
    if args.assetid:
        body['annotatedAssetId'] = args.assetid
    if args.fields:
        params['fields'] = args.fields
    result = httpc.put(f'devices/chromebrowsers/{args.id}', params=params, json=body)
    print_json(result.json())

def deletebrowser(args, httpc):
    """Delete browser."""
    result = httpc.delete(f'devices/chromebrowsers/{args.id}')
    print_json(result.json())

def movebrowsers(args, httpc):
    """Move browsers."""
    if sum(map(bool, [args.ids, args.query, args.file_of_ids])) != 1:
        print('Please specify exactly one of --ids, --query or --file-of-ids')
        sys.exit(1)
    body = {}
    body['org_unit_path'] = args.orgunit
    if args.ids:
        ids = args.ids.split(',')
    elif args.query:
        ids = []
        params = {
            'fields': 'browsers(deviceId),nextPageToken',
            'query': args.query
        }
        while True:
            result = httpc.get('devices/chromebrowsers', params=params)
            browsers = result.json().get('browsers', [])
            ids.extend([browser['deviceId'] for browser in browsers])
            if 'nextPageToken' in result:
                params['pageToken'] = result['nextPageToken']
            else:
                break
    else:
        if not os.path.isfile(args.file_of_ids):
            print(f'ERROR: {args.file_of_ids} does not exist')
            sys.exit(2)
        with open(args.file_of_ids, 'r') as fpointer:
            lines = fpointer.readlines()
        ids = [line.strip() for line in lines]
    id_chunks = list(chunks(ids, 600))
    for id_chunk in id_chunks:
        print(f' moving {len(id_chunk)} browsers...')
        body['resource_ids'] = id_chunk
        result = httpc.post('devices/chromebrowsers/moveChromeBrowsersToOu', json=body)
        print(f'{result.status_code} {result.reason}')


def listtokens(args, httpc):
    """List tokens."""
    params = {}
    if args.orgunit:
        params['orgUnitPath'] = args.orgunit
    if args.query:
        params['query'] = args.query
    if args.fields:
        params['fields'] = args.fields
    tokens = []
    while True:
        result = httpc.get('chrome/enrollmentTokens', params=params).json()
        tokens += result.get('chromeEnrollmentTokens', [])
        if 'nextPageToken' in result:
            params['pageToken'] = result['nextPageToken']
        else:
            break
    print_json(tokens)


def createtoken(args, httpc):
    """Create token."""
    body = {'token_type': 'chromeBrowser'}
    params = {}
    if args.expire:
        body['expire_time'] = args.expire
    if args.orgunit:
        body['org_unit_path'] = args.orgunit
    if args.ttl:
        body['ttl'] = args.ttl
    if args.fields:
        params['fields'] = args.fields
    result = httpc.post('chrome/enrollmentTokens', params=params, json=body)
    print_json(result.json())

def revoketoken(args, httpc):
    """Revoke token."""
    result = httpc.post(f'chrome/enrollmentTokens/{args.id}:revoke')
    print(f'{result.status_code} {result.reason}')


def chunks(full_list, list_length):
    """breaks full_list into a list of lists of length list_length"""
    for i in range(0, len(full_list), list_length):
        yield full_list[i:i+list_length]


def print_json(myjson):
    """Pretty print JSON output."""
    print(json.dumps(myjson, indent=2, sort_keys=True))

def build_http(customer, headers):
    """Build an HTTP object with backoff/retry."""
    retry_strategy = Retry(
        total=7,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    base_url = f'https://www.googleapis.com/admin/directory/v1.1beta1/customer/{customer}/'
    http_client = sessions.BaseUrlSession(base_url=base_url)
    http_client.mount("https://", adapter)
    http_client.headers.update(headers)
    return http_client

def build_credentials(credentials_file, admin):
    """Build authenticated credentials headers."""
    if not os.path.isfile(credentials_file):
        print(f'ERROR: {credentials_file} does not exist')
        sys.exit(2)
    with open(credentials_file, 'rb') as fpointer:
        credentials_data = json.load(fpointer)
    client_id = credentials_data.get('client_id')
    if not client_id:
        print(f'ERROR: {credentials_file} is not valid, no client_id present')
        sys.exit(3)
    headers = {
        'Accept': 'application/json',
        'User-Agent': f'Break19 {__version__} ' \
                'https://github.com/jay0lee/break19'
        }
    creds = Credentials.from_service_account_info(credentials_data)
    creds = creds.with_scopes(SCOPES)
    creds = creds.with_subject(admin)
    request = google.auth.transport.requests.Request()
    try:
        creds.refresh(request)
    except google.auth.exceptions.RefreshError as err:
        print(err)
        admin_url = f'https://admin.google.com/ac/owl/domainwidedelegation' \
                    f'?clientIdToAdd={client_id}' \
                    f'&clientScopeToAdd={",".join(SCOPES)}' \
                    f'&overwriteClientId=true'
        print(f'Please go to:\n\n{admin_url}\n\nto authorize access.')
        sys.exit(1)
    creds.apply(headers)
    return headers


def main(args=None):
    """Main function."""
    args = get_args(args)
    if args.debug:
        http.client.HTTPConnection.debuglevel = 1
    headers = build_credentials(args.credentials_file, args.admin)
    httpc = build_http(args.customer, headers)
    args.func(args, httpc)


if __name__ == '__main__':
    main(sys.argv[1:])
