# iputil

A utility to parse IPs from text and perform GeoIP/RDAP lookups.

## Usage

### Parse

To parse IPs contained within a text file, use the following command:

    $ iputil parse data/list_of_ips.txt

This command will check for the specified text file in the directory in which
it is run. It will store a cache of the IPs found in ``/tmp/.ip_cache``. Use
``--cache-path=PATH`` to specify a different location.

### GeoIP

To lookup the GeoIPs for each IP found within the text file, use the following
command:

    $ iputil geoip

This command expects ``data/GeoLite2-City.mmdb`` to be present in the
directory in whichthis command is run. Use the ``--mmdb-path=PATH`` to specify
a different location for the MaxMind database.

### Filter

To filter IPs using their GeoIP properties use the following command:

    $ iputil filter "city == Los Angeles"

This will display all the IPs located in the city of Los Angeles.

    $ iputil filter "country != JP"

This will display IPs not located in Japan.

    $ iputil filter "country == US and state != CO"

This will display IPs located in the United States, but not in Colorado.

    $ iputil filter "state == UT or state == CA"

This will display IPs located in Utah or California.
