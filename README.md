# LiquiDNS - Zonefile Importer - Version 0.1 (2015 Aug 28)
    Copyright 2015 Treestle B.V.
    
## Usage: 
    ./zoneimporter.py -h                  # Display this help message.
    ./zoneimporter.py -u <username> \
        -p <password>  \
        -f <filename>                     # Parse the zonefile and insert records in LiquiDNS.
## Arguments:
    -h or --help                          Display this help message.
    -f <filename>                         Source zone file (can contain many zones).
        or --file <filename>
    -u <username>                         LiquiDNS Username.
        or --username <username>
    -p <password>                         LiquiDNS Password.
        or --password <password>
    -v or --verbose                       Prints more detailed status messages.
    -V or --version                       Prints the version number of the importer.


## Requirements:
* python3 (Should also work with python 2.7+ - though untested)
* dnslib (python library - can be installed with pip/pip3)
* requests (python library - can be installed with pip/pip3)
* a liquidns.com account
* a zone file (for example format see below) - NOTE: only one zone can be in a file.

### Example zonefile:
    ; example.net [599860]
    $TTL 86400
    @	IN	SOA	ns1.someprovider.com. hostmaster.example.net. 2015082823 14400 14400 1209600 86400
    @		NS	ns1.someprovider.com.
    @		NS	ns2.someprovider.com.
    @		MX	10	ASPMX3.GOOGLEMAIL.COM.
    @		TXT	"v=spf1 mx a ~all"
    @		A	198.51.100.32
    www	CNAME	example.net.
