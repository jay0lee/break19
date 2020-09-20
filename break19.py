import argparse
import http
import pprint
import sys

import google.auth.transport.requests
from google.oauth2.service_account import Credentials

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt import sessions

__version__ = '0.1'
__author__ = 'Jay Lee'


def get_parser():
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

    return parser


def listbrowsers(args):
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
        s = r.get('devices/chromebrowsers', params=params)
        result = s.json()
        browsers += result.get('browsers', [])
        if 'nextPageToken' in result:
            params['pageToken'] = result['nextPageToken']
        else:
            break
    print_json(browsers)

def getbrowser(args):
    params = {}
    if args.fields:
        params['fields'] = args.fields
    s = r.get(f'devices/chromebrowsers/{args.id}', params=params)
    print_json(s.json())


def updatebrowser(args):
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
    s = r.put(f'devices/chromebrowsers/{args.id}', params=params, json=body)
    print_json(s.json())

def deletebrowser(args):
    s = r.delete(f'devices/chromebrowsers/{args.id}')
    print_json(s.json())

def movebrowsers(args):
    body = {}
    body['resource_ids'] = args.ids.split(',')
    body['org_unit_path'] = args.orgunit
    s = r.post('devices/chromebrowsers/moveChromeBrowsersToOu', json=body)
    print(f'{s.status_code} {s.reason}')


def listtokens(args):
    params = {}
    if args.orgunit:
        params['orgUnitPath'] = args.orgunit
    if args.query:
        params['query'] = args.query
    if args.fields:
        params['fields'] = args.fields
    tokens = []
    while True:
        s = r.get('chrome/enrollmentTokens', params=params)
        result = s.json()
        tokens += result.get('chromeEnrollmentTokens', [])
        if 'nextPageToken' in result:
            params['pageToken'] = result['nextPageToken']
        else:
            break
    print_json(tokens)


def createtoken(args):
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
    s = r.post('chrome/enrollmentTokens', params=params, json=body)
    print_json(s.json())

def revoketoken(args):
    s = r.post(f'chrome/enrollmentTokens/{args.id}:revoke')
    print(f'{s.status_code} {s.reason}')


def print_json(json):
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(json)

def build_http(customer):
    retry_strategy = Retry(
        total=7,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    base_url = f'https://www.googleapis.com/admin/directory/v1.1beta1/customer/{customer}/'
    r = sessions.BaseUrlSession(base_url=base_url)
    r.mount("https://", adapter)
    r.headers.update(headers)
    return r


def main(args=None):
    global headers, r
    parser = get_parser()
    args = parser.parse_args(args)
    if args.debug:
        http.client.HTTPConnection.debuglevel = 1
    headers = {'Accept': 'application/json'}
    creds = Credentials.from_service_account_file(args.credentials_file)
    scopes = ['https://www.googleapis.com/auth/admin.directory.device.chromebrowsers']
    creds = creds.with_scopes(scopes)
    creds = creds.with_subject(args.admin)
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    creds.apply(headers)
    r = build_http(args.customer)
    args.func(args)


if __name__ == '__main__':
    main(sys.argv[1:])
