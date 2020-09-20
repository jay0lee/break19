# break19

Tool to interact with the Google Chrome Browser Management Console (CBCM) API

When I was a kid my father had a [CB radio](https://en.wikipedia.org/wiki/Citizens_band_radio) (get it? CB radio CB - "Chrome browser"? OK it's a stretch I admit). "Break one-nine for a radio check" was CB lingo for "can you hear me?" It was all my brother and I really knew to say but boy did we learn some new words from the truckers.

break19 supports all the [CBCM browser](https://support.google.com/chrome/a/answer/9681204?hl=en&ref_topic=9301744) and [token](https://support.google.com/chrome/a/answer/9949706?hl=en&ref_topic=9301744) API calls.

```
$ break19 --help
usage: Break19 [-h] --credentials-file CREDENTIALS_FILE --customer CUSTOMER --admin ADMIN [--debug] {list-browsers,get-browser,update-browser,delete-browser,move-browsers,list-tokens,create-token,revoke-token} ...

positional arguments:
  {list-browsers,get-browser,update-browser,delete-browser,move-browsers,list-tokens,create-token,revoke-token}
    list-browsers       List browsers
    get-browser         Get browser
    update-browser      Update browser
    delete-browser      Delete browser
    move-browsers       Update browsers
    list-tokens         List enrollment tokens
    create-token        Create enrollment token
    revoke-token        Revoke enrollment token

optional arguments:
  -h, --help            show this help message and exit
  --credentials-file CREDENTIALS_FILE
                        location of your service account credentials
  --customer CUSTOMER   Customer ID from admin.google.com > Account > Account settings > Profile.
  --admin ADMIN         Email address of admin user to act as.
  --debug               Show HTTP session details
  

$ break19 --credentials-file ~/GAM/src/oauth2service.json --customer C01wfv983 --admin me@u.jaylee.us list-browsers
[ { 'browserVersions': ['85.0.4183.102'],
    'deviceId': '5505a650-7c37-4364-8c2d-159c444962e0',
    'extensionCount': '22',
    'kind': 'admin#directory#browserdevice',
    'lastActivityTime': '2020-09-20T13:56:55.347Z',
    'lastDeviceUser': 'STANDALONE1\\jayhlee',
    'lastPolicyFetchTime': '2020-09-19T19:29:44.088Z',
    'lastRegistrationTime': '2020-08-31T17:18:08.227Z',
    'machineName': 'STANDALONE1',
    'orgUnitPath': '/',
    'osArchitecture': 'x86_64',
    'osPlatform': 'Windows',
    'osPlatformVersion': 'Windows 10',
    'osVersion': '10.0.17763.1457',
    'policyCount': '8',
    'serialNumber': 'GoogleCloud-B30C8D4C801CF9FFB21D06B129DD6E62',
    'virtualDeviceId': 'f9d98a20-495a-4efd-9eb6-66df1e532f83'}]
```
