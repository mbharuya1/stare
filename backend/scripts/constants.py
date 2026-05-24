"""Static mappings used to decode SCDB integer codes.

SCDB issue-area codebook: http://scdb.la.psu.edu/documentation/documentation.php
Justice IDs:               http://scdb.la.psu.edu/documentation/justices.php
"""
from __future__ import annotations

# SCDB issueArea (1..14). 0 / NaN = unspecified.
ISSUE_AREA = {
    1: "Criminal Procedure",
    2: "Civil Rights",
    3: "First Amendment",
    4: "Due Process",
    5: "Privacy",
    6: "Attorneys",
    7: "Unions",
    8: "Economic Activity",
    9: "Judicial Power",
    10: "Federalism",
    11: "Interstate Relations",
    12: "Federal Taxation",
    13: "Miscellaneous",
    14: "Private Action",
}

# SCDB decisionDirection: 1=conservative, 2=liberal, 3=unspecifiable
DECISION_DIRECTION = {
    1: "conservative",
    2: "liberal",
    3: "unspecifiable",
}

# Justice IDs → last names (modern justices 1946-present, abridged but
# covers everyone who has written a majority opinion in our window).
# Source: SCDB justices documentation.
JUSTICE = {
    78: "Black",         79: "Reed",          80: "Frankfurter",   81: "Douglas",
    82: "Murphy",        83: "Jackson",       84: "Rutledge",      85: "Burton",
    86: "Vinson",        87: "Clark",         88: "Minton",        89: "Warren",
    90: "Harlan2",       91: "Brennan",       92: "Whittaker",     93: "Stewart",
    94: "White",         95: "Goldberg",      96: "Fortas",        97: "Marshall",
    98: "Burger",        99: "Blackmun",     100: "Powell",       101: "Rehnquist",
    102: "Stevens",     103: "OConnor",      104: "Scalia",       105: "Kennedy",
    106: "Souter",      107: "Thomas",       108: "Ginsburg",     109: "Breyer",
    110: "Roberts",     111: "Alito",        112: "Sotomayor",    113: "Kagan",
    114: "Gorsuch",     115: "Kavanaugh",    116: "Barrett",      117: "Jackson3",
}
