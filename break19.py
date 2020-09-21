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

__version__ = '0.1'
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

    listbrowsers_p = subparsers.add_parser('list-browsers', help='List browsers')
    listbrowsers_p.add_argument('--orgunit', help='OrgUnit to scope results')
    listbrowsers_p.add_argument('--orderby', help='Sort results by property')
    projection_choices = ['BASIC', 'FULL']
    listbrowsers_p.add_argument('--projection', default='BASIC', choices=projection_choices,
                                help='retrieve basic or full browser details')
    listbrowsers_p.add_argument('--query', help='Query to scope results')
    sort_choices = ['ASCENDING', 'DESCENDING']
    listbrowsers_p.add_argument('--sortorder', default='ASCENDING', choices=sort_choices,
                                help='Sort order')
    listbrowsers_p.add_argument('--fields', help='Limit fields retrieved and output.')
    listbrowsers_p.set_defaults(func=listbrowsers)

    getbrowser_p = subparsers.add_parser('get-browser', help='Get browser')
    getbrowser_p.add_argument('--id', required=True,
                              help='deviceId of the browser to get')
    getbrowser_p.add_argument('--fields', help='Limit fields retrieved and output.')
    getbrowser_p.set_defaults(func=getbrowser)

    updatebrowser_p = subparsers.add_parser('update-browser', help='Update browser')
    updatebrowser_p.add_argument('--id', required=True,
                                 help='deviceId of the browser to update')
    updatebrowser_p.add_argument('--user', help='user of the browser')
    updatebrowser_p.add_argument('--location', help='location of the browser')
    updatebrowser_p.add_argument('--notes', help='notes of the browser')
    updatebrowser_p.add_argument('--assetid', help='asset tag id of the browser')
    updatebrowser_p.add_argument('--fields', help='Limit fields retrieved and output.')
    updatebrowser_p.set_defaults(func=updatebrowser)

    deletebrowser_p = subparsers.add_parser('delete-browser', help='Delete browser')
    deletebrowser_p.add_argument('--id', required=True,
                                 help='deviceId of the browser to delete')
    deletebrowser_p.set_defaults(func=deletebrowser)

    movebrowsers_p = subparsers.add_parser('move-browsers', help='Update browsers')
    movebrowsers_p.add_argument('--ids', required=True,
                                help='comma-seperated deviceIds of the browsers to move')
    movebrowsers_p.add_argument('--orgunit', required=True,
                                help='Org Unit location to move browsers')
    movebrowsers_p.set_defaults(func=movebrowsers)

    listtokens_p = subparsers.add_parser('list-tokens', help='List enrollment tokens')
    listtokens_p.add_argument('--orgunit', help='OrgUnit to scope results')
    listtokens_p.add_argument('--query', help='Query to scope results')
    listtokens_p.add_argument('--fields', help='Limit fields retrieved and output.')
    listtokens_p.set_defaults(func=listtokens)

    createtoken_p = subparsers.add_parser('create-token', help='Create enrollment token')
    createtoken_p.add_argument('--expire',
                               help='Expire time of the created enrollment ' \
                                       'token, in "yyyy-MM-ddThh:mm:ssZ" ' \
                                       'format.')
    createtoken_p.add_argument('--orgunit',
                               help='The organization unit to create an ' \
                                       'enrollment token for. If this' \
                                       'field is not specified, the ' \
                                       'enrollment token is created for the ' \
                                       'root organization unit.')
    createtoken_p.add_argument('--ttl', help='Life of the created enrollment ' \
            'token, encoded in seconds with an “s” suffix. Eg, for a token ' \
            'to live for 1 hour, this field should be set to “3600s”.')
    createtoken_p.set_defaults(func=createtoken)
    createtoken_p.add_argument('--fields', help='Limit fields retrieved and output.')

    revoketoken_p = subparsers.add_parser('revoke-token', help='Revoke enrollment token')
    revoketoken_p.add_argument('--id', required=True,
                               help='permanent ID of the token to revoke')
    revoketoken_p.set_defaults(func=revoketoken)

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
    body = {}
    body['resource_ids'] = args.ids.split(',')
    body['org_unit_path'] = args.orgunit
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
