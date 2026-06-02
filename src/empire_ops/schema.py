"""Live Empire Ops base schema — table and field IDs.

Generated from the base created in Phase 0 (base ``applx48uo2056erUB`` in
"My First Workspace"). Routines reference fields by these IDs so renaming a
column in the Airtable UI never breaks code. Keep in sync with
docs/empire-ops-base.md; regenerate via ``list_tables_for_base`` if the schema
changes.
"""

from __future__ import annotations

BASE_ID = "applx48uo2056erUB"


class ContentQueue:
    TABLE_ID = "tbl7xBGNGjUTaalMN"
    TITLE = "fldLlL3l7RrtuqtE9"
    PROMPT = "fldoqc134wNuWcePe"
    BRAND = "fld4O0WTiBiZDlvId"
    ASSET_TYPE = "fldI1pfh5X0ssZXEm"
    STATUS = "fldsWunP646es7S0X"
    GUARDRAIL_TIER = "fldbDtPGIBwM4E1xP"
    OUTPUT_URL = "fldaogSijTxDSrJPI"
    CLOUDINARY_FOLDER = "fldaWZpaIH0iHpbAo"
    SCHEDULED_FOR = "fldd9818SBIMI4PIA"
    NOTES = "fld74tNi4oz70ZHOU"
    CREATED = "fldodieDmNTSNyIQJ"


class MusicCatalog:
    TABLE_ID = "tblzrCOp4c9O7fChh"
    TRACK_TITLE = "fldebXgcN0x2LRoFM"
    STATUS = "fldBqnmuawS6GB1Ti"
    BPM = "fldGrJw2ArfFoZy3u"
    KEY = "fldeSZsvQOsC9GHZ7"
    DIRECTION = "fld5a6fXFbeJp3V1y"
    OPEN_VERSE = "fldbizAZz6kolmP5k"
    COVER_ART_QUEUED = "fld0kUrFHbpa2iTka"
    DRIVE_LINK = "fldoOkMOZZmga5WF3"
    BRAND = "fldqaQt3WcpuC1bFN"
    NOTES = "fldNHtc9Z5EkjBKsM"


class DropCalendar:
    TABLE_ID = "tblNRn8TJ5MOadYtz"
    DROP_NAME = "fldS6D2USek6lpRkC"
    BRAND = "fldZvZbO9XFjIzmrJ"
    DROP_DATE = "fldPmsjakorapoXNt"
    CHANNEL = "fldtB3WaqAe1tV21c"
    STATUS = "fld1aNR5TOs9KuAAX"
    LINKED_ASSETS = "fldR4qVcd3anTPQQ9"
    NOTES = "fldDs8wuH0ZJCRAha"


class Leads:
    TABLE_ID = "tblIlXb2ygjyN5lFZ"
    NAME = "fld5EE0hnlhh7nfxo"
    SOURCE = "fldDnpWJ7hvelzrVF"
    EMAIL = "fldfWZEzvH2NqG1hY"
    PHONE = "fldjdTu96P9eiIk7H"
    REQUEST = "fldFOaA7DgHPjN0Ca"
    STATUS = "fldv258q3lTP4eUlp"
    DRAFT_RESPONSE = "fld9fErredV0aaEin"
    RECEIVED = "fldD57ioRVDu0DDD6"


class MoneyDigestLog:
    TABLE_ID = "tblqZlbdD5zjsIGD6"
    DIGEST_DATE = "fld5tVXbGx2aLZm2e"
    SUMMARY = "fldRxIErNe6v9lze4"
    CASH_POSITION = "fld2TftLedIjoTggy"
    SOURCES = "fldY60LfoOSMYaFDP"
    FLAGS = "fldm1fuO0c0QXEJwB"
    TIER = "fld7FQ4DJPIJ2K8Gk"
    GENERATED_AT = "fldqA5IZNKtCOZUGT"


class NeedsApproval:
    TABLE_ID = "tblkmcJDeZgMTCl7j"
    ITEM = "fldpLQULFdaXZhMWC"
    TYPE = "fldLyWIEYvOZa12u0"
    BRAND = "fldHPjlTTKbCiwtA8"
    PREVIEW_LINK = "fldg9gWLHBAT3RoZK"
    GUARDRAIL_TIER = "fld4upVJ8RJTDCFiH"
    APPROVAL_STATUS = "fld6Khcfh1vhUi71b"
    SOURCE_TABLE = "fldMRvL3xEJa79SzO"
    SOURCE_RECORD = "fldfLMwrEXPi3xja8"
    SUMMARY = "fldmpL1eI9p1XH5mW"
    SUBMITTED = "fldsv9YK6GfrEIna0"
    DECIDED = "fldQWkTBdm4882Hpf"
