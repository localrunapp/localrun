from enum import Enum


class DNSRecordType(str, Enum):
    """DNS record types"""

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"
    MX = "MX"
    SRV = "SRV"
