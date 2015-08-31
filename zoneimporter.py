#!/usr/bin/env python3

_name_ = "LiquiDNS Zonefile Importer"
_copyright_ = "Copyright 2015 Treestle B.V."
_version_ = "0.1"

import dnslib
import getopt
import sys
import requests
import json

verbose = False

def usage():
    print("""
LiquiDNS - Zonefile Importer - Version 0.1 (2015 Aug 28)
    Copyright 2015 Treestle B.V.


Usage: 
    ./zoneimporter.py -h                  Display this help message.
    ./zoneimporter.py -u <username> \\
        -p <password>  \\
        -f <filename>                     Parse the zonefile and insert records in LiquiDNS.


Arguments:
    -h or --help                          Display this help message.
    -f <filename>                         Source zone file (can contain many zones).
        or --file <filename>
    -u <username>                         LiquiDNS Username.
        or --username <username>
    -p <password>                         LiquiDNS Password.
        or --password <password>
    -v or --verbose                       Prints more detailed status messages.
    -V or --version                       Prints the version number of the importer.
    """)


def parse_options(opts):
    s_zone = ""
    s_username = ""
    s_password = ""
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-V", "--version"):
            print(_name_)
            print(_copyright_)
            print(_version_)
            sys.exit()
        elif opt in ("-v", "--verbose"):
            print("Verbose printing enabled")
            global verbose
            verbose = True
        elif opt in ("-f", "--file"):
            try:
                f_zonefile = open(arg, "r")
                s_zone = f_zonefile.read()
            except:
                print("could not open file")
                sys.exit()
        elif opt in ("-u", "--username"):
            s_username = arg
        elif opt in ("-p", "--password"):
            s_password = arg
    return (s_username, s_password), s_zone


def parse_zonefile(s_zone):
    l_lines = s_zone.split("\n")
    s_apex_domain = l_lines[0].split(" ")[1]
    i_default_ttl = int(l_lines[1].split(" ")[1])
    l_zone = []
    print("domain: {}.".format(s_apex_domain))
    for s_line in l_lines[2:-1]:
        rr_record = dnslib.RR.fromZone(s_line)[0]
        s_label = str(rr_record.rname)
        if s_label != ".":
            s_label = s_label+s_apex_domain
        else:
            s_label = s_apex_domain
        rr_record.rname = dnslib.DNSLabel(s_label)
        l_zone.append(rr_record)
    if verbose:
        print_l_zone(l_zone) 
    return l_zone


def print_l_zone(l_zone):
    print ("\n\n")
    print ("The zone was parsed as follows: \n\n")
    for rr_record in l_zone:
        print(rr_record)
    c_correct = ""
    while c_correct not in ("Y", "N", "y", "n"):
        c_correct = input("Is this correct (Y/n)? ")
        if c_correct == "":
            c_correct = "Y"
    if c_correct in ("n", "N"):
        print ("Canceled by user")
        sys.exit(2)


class API(object):

    def __init__(self, t_login):
        self.session, self.csrftoken = self.login(t_login)

    def login(self, t_login):
        try:
            s = requests.Session()
            s.head('https://liquidns.com/accounts/login/')
            csrftoken = s.cookies.get_dict()['csrftoken']
            login_data = dict(login=t_login[0], password=t_login[1], csrfmiddlewaretoken=csrftoken, next='/')
            headers = {'Content-Type': "application/x-www-form-urlencoded", 'referer': "https://liquidns.com/accounts/login/" }
            s.post('https://liquidns.com/accounts/login/', data=login_data, headers=headers)
            csrftoken = s.cookies.get_dict()['csrftoken']
            if verbose:
                print("Login sucessful")
            return s, csrftoken
        except Exception as e:
            print("Failed to login")
            print("Error was: \n{}".format(e))
            sys.exit(2)

    def push_domain(self, s_label):
        headers = {'Content-Type': "application/x-www-form-urlencoded", 'referer': "https://liquidns.com/api/v2/domains/" }
        data={"domain": s_label, "csrfmiddlewaretoken":self.csrftoken, "dnssec": False}
        r = self.session.post('https://liquidns.com/api/v2/domains/', data=data, headers=headers)
        if verbose:
            print(r.ok)
            print(r.reason)

    def push_record(self, s_label, s_data, i_type):
        headers = {'Content-Type': "application/x-www-form-urlencoded", 'referer': "https://liquidns.com/api/v2/records/" }
        data={"domain": s_label, "type": i_type, "record": s_data,  "label": "from imported from zonefile", "csrfmiddlewaretoken":self.csrftoken}
        r = self.session.post('https://liquidns.com/api/v2/records/', data=data, headers=headers)
        if verbose:
            print(r.ok)
            print(r.reason)
    
    def push_zone(self, l_zone):
        l_unique_labels = list()
        for rr_record in l_zone:
            s_label = str(rr_record.rname)[:-1] # strip the trailing '.'
            s_data = str(rr_record.rdata)
            i_type = int(rr_record.rtype)
            ## only push unique domain labels (E.G. subdomain.domain.tld)
            if s_label not in l_unique_labels:
                l_unique_labels.append(s_label)
                if verbose:
                    print("pushing new domain: {}".format(s_label))
                self.push_domain(s_label)
            ## clean and push records
            if verbose:
                print("pushing new record")
            if i_type not in (2, 6):
                self.push_record(s_label, s_data, i_type)
            elif i_type == 6:
                ## clean record
                l_parts = s_data.split(" ")  # split the data into a list 
                l_parts[0] = "ns1.liquidns.net" # replace the first element
                s_data = " ".join(l_parts) # join it back together using white space as the element seperator
                ## push record
                self.push_record(s_label, s_data, i_type)


def api_push(t_login, l_zone):
    try:
        if verbose:
            print("Logging in with: \nusername: {}\npassword: {}".format(*t_login))
        api = API(t_login)
        api.push_zone(l_zone)
    except Exception as e:
        print("API ERROR! \n\n {}".format(e))
    

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hvVf:u:p:", ["help", "file=", "username=", "password=", "version", "verbose"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    t_login, s_zone = parse_options(opts)
    if "" in (s_zone, t_login[0], t_login[1]):
        usage()
        sys.exit(2)
    if len(args) > 0:
        usage()
    l_zone = parse_zonefile(s_zone)
    api_push(t_login, l_zone)


if __name__ == "__main__":
    main(sys.argv[1:])

    
