#!/bin/env python3
# title="$icon_usr Sync Contacts from CardDAV"
import os
import sys
import uuid
import csv
import getpass
from io import StringIO

import carddav
import vobject
import argparse

import vcard_to_tsv
from defaults import *


def download(url, user, passwd, auth, verify, filename):
    print('[i] Downloading from', url, '...')
    print('[i] Downloading the addressbook...')
    dav = carddav.PyCardDAV(url, user=user, passwd=passwd, auth=auth,
                            verify=verify)
    abook = dav.get_abook()
    nCards = len(abook.keys())
    print('[i] Found', nCards, 'cards.')

    f = open(filename, "w")

    curr = 1
    for href, etag in abook.items():
        print('\r[i] Fetching', curr, 'of', nCards, )
        sys.stdout.flush()
        curr += 1
        card = dav.get_vcard(href)
        tsv = vcard_to_tsv.vcard_to_tsv(card.decode('utf8'))
        if not tsv == "":
            f.write(tsv + '\n')
    print('')
    f.close()
    print('[i] All saved.')


def sync(url, user, passwd, auth, verify, filename):
    print('[i] Syncing from', url, '...')
    print('[i] Getting the local addressbook...')
    dav = carddav.PyCardDAV(url, user=user, passwd=passwd, auth=auth,
                            verify=verify)
    abook = dav.get_abook()
    nCards = len(abook.keys())
    print('[i] Found', nCards, 'cards.')
    local = dict()
    remote = dict()
    with open(filename, "r") as flocal:
        tsv_file = csv.reader(flocal, delimiter="\t")
        for line in tsv_file:
            local[line.join("\t")] = bool(1)
    f = open(filename, "w")
    curr = 1
    print('[i] Downloading the remote addressbook...')
    for href, etag in abook.items():
        print('\r[i] Fetching', curr, 'of', nCards, )
        sys.stdout.flush()
        curr += 1
        card = dav.get_vcard(href)
        tsv = vcard_to_tsv.vcard_to_tsv(card.decode('utf8'))
        if not tsv == "":
            remote[tsv] = bool(1)
            #f.write(tsv + '\n')
    print('')
    print('[i] Mixing everything...')
    local.update(remote)
    nCards = len(local.keys())
    curr = 1
    for mix, b in local.items():
        print('\r[i] Writing', curr, 'of', nCards, )
        sys.stdout.flush()
        curr += 1
        if not mix == "":
            f.write(mix + '\n')
    f.close()
    print('[i] All saved.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str, help="CardDav URL", default=URL)
    parser.add_argument("-u", "--user", type=str, help="CardDav user", default=USERNAME)
    parser.add_argument("-p", "--password", type=str, help="CardDav password. Omit to prompt for password",
                        default=PASSWORD)
    parser.add_argument("--no-cert-verify", help="Do not verify https certificate", action="store_true")
    parser.add_argument('--digest', action="store_true", help="Use digest authentication")
    parser.add_argument("-f", "--tsv-file", default=TSV_FILE, help=F'Output TSV file name (defaults to "{TSV_FILE}")')
    args: argparse.Namespace = parser.parse_args()

    url = args.url

    user = args.user
    passwd = args.password
    auth = 'digest' if args.digest else 'basic'
    verify = not args.no_cert_verify
    file:str = args.tsv_file

    if file.startswith("~"):
        file = os.path.expanduser(file)

    if passwd is None:
        passwd = getpass.getpass(user + '\'s password: ')

    sync(url, user, passwd, auth, verify, file)


if __name__ == '__main__':
    sys.exit(main())
