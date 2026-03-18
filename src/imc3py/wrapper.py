from __future__ import annotations
from dataclasses import dataclass
import fnmatch
import mmap
import numpy as np
import os
import pandas as pd
import struct
from typing import Union

VALID_LANGUAGES = dict()
VALID_LANGUAGES[932] = [0x11] # japan
VALID_LANGUAGES[936] = [0x804] # china
VALID_LANGUAGES[949] = [0x412] # korea
VALID_LANGUAGES[950] = [0x404] # taiwan
VALID_LANGUAGES[1250] = [0x402] # eastern europe
VALID_LANGUAGES[1251] = [0x419] # cyrillic
VALID_LANGUAGES[1252] = [0x407, 0x409, 0x40c, 0x410, 0x40a, 0x41d] # western europe
VALID_LANGUAGES[1254] = [0x419] # turk

VALID_KEYS = [b'|CB1', b'|CL1', b'|CO1', b'|Cd1', b'|CA1', b'|CG1', b'|Ct1', b'|CT1', b'|CV1', b'|CC1', 
              b'|CM1', b'|CH1', b'|CH2', b'|Cq1', b'|CX1', b'|CZ1', b'|CD1', b'|Cw1', b'|Ce1', b'|CN1', 
              b'|CP1', b'|RR1', b'|RN1', b'|RC5', b'|RT1', b'|Ri1', b'|RE1', b'|CS1', b'|CJ1', b'|NU1',
              b'|CE1']

HEADER_KEYS = ['|CB1', '|CL1', '|CO1', '|CA1']
UNIQUE_KEYS = ['|CB1', '|CL1', '|CO1', '|Cd1', '|CA1']

COMPONENTCOMBINATION_2COMPONENTS = [2, 3, 4, 5, 6]

NUMERICAL_FORMATS = {
    1: {'format':'UINT8', 'bytes': 1, 'npformat': 'uint8'},
    2: {'format':'SINT8', 'bytes': 1, 'npformat': 'int8'},
    3: {'format':'UINT16', 'bytes': 2, 'npformat': 'uint16'},
    4: {'format':'SINT16', 'bytes': 2, 'npformat': 'int16'},
    5: {'format':'UINT32', 'bytes': 4, 'npformat': 'uint32'},
    6: {'format':'SINT32', 'bytes': 4, 'npformat': 'int32'},
    7: {'format':'FLT', 'bytes': 4, 'npformat': 'float32'},
    8: {'format':'DBL', 'bytes': 8, 'npformat': 'float64'},
    10: {'format':'TSA', 'bytes': 6, 'npformat': ''},
    12: {'format':'UINT64', 'bytes': 8, 'npformat': 'uint64'},
    13: {'format':'UINT48', 'bytes': 6, 'npformat': ''},
    14: {'format':'SINT64', 'bytes': 8, 'npformat': 'int64'},
}

MAPPING_FORMATS = {
        'FLT': ('<f', 4),
        'DBL': ('<d', 8),
        'SINT8': ('<b', 1),
        'SINT16': ('<h', 2),
        'SINT32': ('<l', 4),
        'UINT8': ('<B', 1),
        'UINT16': ('<H', 2),
        'UINT32': ('<I', 4),
        'UINT64': ('<Q', 8),
    }

class IMC3Error(Exception):
    pass

@dataclass
class IMC3Header:
    # from |CB1
    dwMagic1: int
    dwMagic2: int
    bVariant: int
    bCs: int
    bUnicode: int
    bCompr: int
    TimeZone: int
    wSummertime: int
    VersionMajor: int
    VersionMinor: int
    # from |CL1
    wCodePage: int
    wLanguage: int
    # from |CO1
    strFileProducer: str
    strFileComment: str
    # from |CA1
    dwCountGroups: int
    dwCountNamedChannels: int
    dwCountIndexChannels: int
    dwCountTextVars: int
    dwCountSingleValues: int

@dataclass
class IMC3Group:
    id: int
    name: str

@dataclass
class IMC3Textvariable:
    group_id: int
    name: str
    comment: str
    value: str

@dataclass
class IMC3Textarray:
    group_id: int
    countElements: int
    name: str
    comment: str
    value: list

@dataclass
class IMC3Value:
    group_id: int
    dTime: float
    value: float
    numericalFormat: int
    name: str
    comment: str
    unit: str

@dataclass
class IMC3Channel:
    cmp1Values: list
    cmp2Values: list
    # from |CC1 key
    dwIndexChannel: int
    dx: float
    x0: float
    group_id: int
    dwDefaultChunkBytes: int
    flags: int
    pretriggerUse: int
    componentCombination: int
    xUnit: str
    numComponents: int
    name: str
    comment: str
    dwEnvelopeReduction: int
    triggertime: float
    uEffectiveLengBytes:int
    uChunkBytes: int
    uEnvelopeBytes:int
    # first component
    cmp1numericalFormat: int
    cmp1additionalSpecifier: int
    cmp1scaleFactor: float
    cmp1scaleOffset: float
    cmp1Unit: str
    cmp1Count: int
    # second component
    cmp2numericalFormat: int
    cmp2additionalSpecifier: int
    cmp2scaleFactor: float
    cmp2scaleOffset: float
    cmp2Unit: str
    cmp2Count: int

class IMC3File:
    def __init__(self, path: Union[str, os.PathLike]):
        # read binary data from dat file
        self.path = str(path)
        self.fd = open(self.path, 'rb')
        self.mm = mmap.mmap(self.fd.fileno(), 0, access=mmap.ACCESS_READ)

        # read file and check for keys to read later
        self.keys = self._get_keys()

        # read header
        self.header = self._parse_header()

        # check if number of text array and variables matches info from |CA1
        keysList = self.keys.keys()
        lenCT = 0
        if '|CT1' in keysList: 
            lenCT = len(self.keys['|CT1'])
        lenCt = 0
        if '|Ct1' in keysList: 
            lenCt = len(self.keys['|Ct1'])

        if self.header.dwCountTextVars != lenCT + lenCt:
            raise IMC3Error('Number of text arrays & variables not matching |CA1 definition')
        
        # read groups
        self.groups = self._read_groups()

        # read single values
        self.singleValues = self._read_single_values()
        
        # read text variables from file
        self.textVariables = self._read_text_variables()

        # read text arrays from file
        self.textArrays = self._read_text_arrays()

        # read channels
        if self.header.dwCountNamedChannels != self.header.dwCountIndexChannels:
            raise IMC3Error('dwCountNamedChannels != dwCountIndexChannels, check cause')

        self.rawOffset = self.keys["|RN1"][0]['start'] + 4
        self.channels = self._read_channels()

        # validation with ending block
        self._validate()

    def close(self):
        try: 
            self.mm.close()
        finally: 
            self.fd.close()

    def __enter__(self):
        return self
    
    def __exit__(self, *a): 
        self.close()

    def _get_keys(self):
        # go trough entire file to get keys and their position inside the file
        # remember: read from top, until key |RN1. then read from bottom up to |RE1
        mm = self.mm
        
        # store occuring keys with start & end position in a dict
        # dict contains list of occurences for each key (dict-key = imc3-key)
        # in list is a dict with info about this occurence (start, end)
        imcKeys = {}

        # check imc3 format
        chunk = mm[0:8]
        if chunk != b'|imc3,1;':
            raise IMC3Error('Not an IMC3 file')
        
        # go trough file after imc3 format indicator, until |RN1 is reached
        i = 7
        maxLen = len(mm)
        oldKey = None
        while True:
            i += 1
            # check if data is available
            if i >= maxLen:
                break

            # see if current byte is a | to indicate start of new key
            if mm[i] == 0x7c:
                if isValidKey(mm[i : i+4]):
                    # detected start of new key
                    newKey = mapData(mm, i, 'STR', strLen=4)

                    # save end of old key
                    if oldKey:
                        imcKeys[oldKey][-1]['end'] = i

                    # save start of new key
                    if newKey in imcKeys.keys():
                        # key was found previously
                        # check if this key can occur more than once
                        if newKey in UNIQUE_KEYS:
                            raise IMC3Error('Key occurred more than once')
                        
                        # append entry to list
                        imcKeys[newKey].append({'start': i})
                    else:
                        # entirely new key found, add new list to dict
                        imcKeys[newKey] = [{'start': i}]

                    if newKey == '|RN1':
                        break

                    i += 3
                    oldKey = newKey

        # go trough file from bottom up , until |RE1 is reached
        i = maxLen
        iEnd = maxLen
        while True:
            i -= 1
            # check if data is available
            if i < 0:
                break

            # see if current byte is a | to indicate start of new key
            if mm[i] == 0x7c:
                if isValidKey(mm[i : i+4]):
                    # detected start of new key
                    newKey = mapData(mm, i, 'STR', strLen=4)

                    # save start of new key
                    if newKey in imcKeys.keys():
                        # key was found previously
                        # check if this key can occur more than once
                        if newKey in UNIQUE_KEYS:
                            raise IMC3Error('Unique key occurred more than once')
                        
                        # append entry to list
                        imcKeys[newKey].insert(0, {'start': i, 'end': iEnd})
                    else:
                        # entirely new key found, add new list to dict
                        imcKeys[newKey] = [{'start': i, 'end': iEnd}]

                    if newKey == '|RE1':
                        break

                    iEnd = i

        return imcKeys
    
    def _parse_header(self) -> IMC3Header:
        # Reads header of imc3 file and returns all file header information
        # Key 1 = |CB1 (Beginning, always)
        # Key 2 = |CL1 (Language, always)
        # Key 3 = |CO1 (Origin, always)
        # Key 4 = |CA1 (Count Dataobjects, always)
        mm = self.mm

        # go through every header key
        for key in HEADER_KEYS:
            chunk = mm[self.keys[key][0]['start'] : self.keys[key][0]['end']]

            # handle chunk data
            match key:
                case '|CB1': # Beginning
                    dwMagic1 = mapData(chunk, 4, 'UINT32')
                    dwMagic2 = mapData(chunk, 8, 'UINT32')
                    bVariant = mapData(chunk, 12, 'UINT8')
                    bCs = mapData(chunk, 13, 'UINT8')
                    bUnicode = mapData(chunk, 14, 'UINT8')
                    bCompr = mapData(chunk, 15, 'UINT8')
                    TimeZone = mapData(chunk, 16, 'SINT16')
                    wSummertime = mapData(chunk, 18, 'UINT16')
                    VersionMajor = mapData(chunk, 20, 'UINT16')
                    VersionMinor = mapData(chunk, 22, 'UINT16')
                    if VersionMajor != 1:
                        raise IMC3Error('Wrong version, VersionMajor not 1')
                
                case '|CL1': # Language
                    wCodePage = mapData(chunk, 4, 'UINT16')
                    wLanguage = mapData(chunk, 6, 'UINT16')
                    if not isLanguageValid(wCodePage, wLanguage):
                        raise IMC3Error('wCodePage & wLanguage not matching')

                case '|CO1': # Origin
                    lenStrFileProducer = mapData(chunk, 4, 'UINT16')
                    strFileProducer = mapData(chunk, 6, 'STR', strLen=lenStrFileProducer)
                    lenStrFileComment = mapData(chunk, 6+lenStrFileProducer, 'UINT16')
                    strFileComment = mapData(chunk, 8+lenStrFileProducer, 'STR', strLen=lenStrFileComment)
                
                case '|CA1': # Origin
                    dwCountGroups = mapData(chunk, 4, 'UINT32')
                    dwCountNamedChannels = mapData(chunk, 8, 'UINT32')
                    dwCountIndexChannels = mapData(chunk, 12, 'UINT32')
                    dwCountTextVars = mapData(chunk, 16, 'UINT32')
                    dwCountSingleValues = mapData(chunk, 20, 'UINT32')

        return IMC3Header(
            # from |CB1
            dwMagic1= dwMagic1,
            dwMagic2= dwMagic2,
            bVariant= bVariant,
            bCs= bCs,
            bUnicode= bUnicode,
            bCompr= bCompr,
            TimeZone= TimeZone,
            wSummertime= wSummertime,
            VersionMajor= VersionMajor,
            VersionMinor= VersionMinor,
            # from |CL1
            wCodePage= wCodePage,
            wLanguage= wLanguage,
            # from |CO1
            strFileProducer= strFileProducer,
            strFileComment= strFileComment,
            # from |CA1
            dwCountGroups= dwCountGroups,
            dwCountNamedChannels= dwCountNamedChannels,
            dwCountIndexChannels= dwCountIndexChannels,
            dwCountTextVars= dwCountTextVars,
            dwCountSingleValues= dwCountSingleValues
        )

    def _parse_group(self, id) -> IMC3Group:
        # Reads group definition from imc3 file and returns IMC3Group object
        # Key 1 = |CG1 (FAMOS Group, always)
        # Key 2 = |CP1 (Properties, optional) TODO, not implemented yes
        chunk = self.mm[self.keys['|CG1'][id]['start'] : self.keys['|CG1'][id]['end']]

        dwIndexGroup = mapData(chunk, 4, 'UINT32')
        lenStrName = mapData(chunk, 8, 'UINT16')
        strName = mapData(chunk, 10, 'STR', strLen=lenStrName)

        return IMC3Group(
            id = dwIndexGroup,
            name = strName
        )

    def _parse_single_value(self, id) -> IMC3Value:
        # Reads single value from imc3 file and returns IMC3Value object
        # Key 1 = |CV1 (Single value, always)
        # Key 2 = |CP1 (Properties, optional) TODO, not implemented yes
        chunk = self.mm[self.keys['|CV1'][id]['start'] : self.keys['|CV1'][id]['end']]
        
        dwIndexGroup = mapData(chunk, 4, 'UINT32')
        dTime = mapData(chunk, 8, 'DBL')
        numericalFormat = mapData(chunk, 24, 'UINT8')
        binaryNumerical = mapSingleValue(chunk, 16, numericalFormat)

        tmp = 25
        lenStrName = mapData(chunk, tmp, 'UINT16')
        strName = mapData(chunk, tmp + 2, 'STR', strLen=lenStrName)
        
        if dwIndexGroup != 0:
            strName = self.get_group_by_id(dwIndexGroup).name + ':' + strName

        tmp = tmp + 2 + lenStrName
        lenStrComment = mapData(chunk, tmp, 'UINT16')
        strComment = mapData(chunk, tmp + 2, 'STR', strLen=lenStrComment)
        
        tmp = tmp + 2 + lenStrComment
        lenStrUnit = mapData(chunk, tmp, 'UINT16')
        strUnit = mapData(chunk, tmp + 2, 'STR', strLen=lenStrUnit)

        return IMC3Value(
            group_id = dwIndexGroup,
            dTime = dTime,
            value = binaryNumerical,
            numericalFormat = numericalFormat,
            name = strName,
            comment = strComment,
            unit = strUnit
        ) 

    def _parse_single_text_variable(self, id) -> IMC3Textvariable:
        # Reads single text variable from imc3 file and returns IMC3Textvariable object
        # Key 1 = |Ct1 (FAMOS Textvariable, always)
        # Key 2 = |CP1 (Properties, optional) TODO, not implemented yet
        chunk = self.mm[self.keys['|Ct1'][id]['start'] : self.keys['|Ct1'][id]['end']]

        dwIndexGroup = mapData(chunk, 4, 'UINT32')

        tmp = 8
        lenStrName = mapData(chunk, tmp, 'UINT16')
        strName = mapData(chunk, tmp + 2, 'STR', strLen=lenStrName)
        
        if dwIndexGroup != 0:
            strName = self.get_group_by_id(dwIndexGroup).name + ':' + strName

        tmp = tmp + 2 + lenStrName
        lenStrComment = mapData(chunk, tmp, 'UINT16')
        strComment = mapData(chunk, tmp + 2, 'STR', strLen=lenStrComment)
        
        tmp = tmp + 2 + lenStrComment
        lenStrContent = mapData(chunk, tmp, 'UINT32')
        strContent = mapData(chunk, tmp + 4, 'STR', strLen=lenStrContent)

        return IMC3Textvariable(
            group_id = dwIndexGroup,
            name = strName,
            comment = strComment,
            value = strContent
        ) 

    def _parse_single_text_array(self, id) -> IMC3Textarray:# Reads single text variable from imc3 file and returns IMC3Textvariable object
        # Key 1 = |CT1 (FAMOS Textarray, always)
        # Key 2 = |CP1 (Properties, optional) TODO, not implemented yet
        chunk = self.mm[self.keys['|CT1'][id]['start'] : self.keys['|CT1'][id]['end']]

        dwIndexGroup = mapData(chunk, 4, 'UINT32')
        dwCountElements = mapData(chunk, 8, 'UINT32')
        
        tmp = 12
        lenStrName = mapData(chunk, tmp, 'UINT16')
        strName = mapData(chunk, tmp + 2, 'STR', strLen=lenStrName)
        
        if dwIndexGroup != 0:
            strName = self.get_group_by_id(dwIndexGroup).name + ':' + strName

        tmp = tmp + 2 + lenStrName
        lenStrComment = mapData(chunk, tmp, 'UINT16')
        strComment = mapData(chunk, tmp + 2, 'STR', strLen=lenStrComment)

        tmp = tmp + 2 + lenStrComment
        content = list()

        for i in range(dwCountElements):
            lenValue = mapData(chunk, tmp, 'UINT32')
            content.append(mapData(chunk, tmp + 4, 'STR', strLen=lenValue))
            tmp = tmp + 4 + lenValue

        return IMC3Textarray(
            group_id = dwIndexGroup,
            countElements = dwCountElements,
            name = strName,
            comment = strComment,
            value = content
        ) 

    def _parse_channel(self, id, cm_offset) -> IMC3Channel:# Reads single text variable from imc3 file and returns IMC3Textvariable object
        # Key  1 = |CC1 (Channel base, always)
        # Key  2 = |CM1 (Component, always)
        # Key  3 = |CM1 (Component, only in channels with 2 components)
        # Key  4 = |CH1 (Offline Trigger, always)
        # Key  5 = |Cq1 (Previous , optional) TODO, not implemented yet
        # Key  6 = |Cw1 (Famos Events Description, optional) TODO, not implemented yet
        # Key  7 = |CZ1 (z-coordinate, optional) TODO, not implemented yet
        # Key  8 = |CX1 (Extraction rules with TSA, optional) TODO, not implemented yet
        # Key  9 = |CD1 (Dispaly, optional) TODO, not implemented yet
        # Key 10 = |CN1 (Channel name, always)
        # Key 11 = |CP1 (Properties, optional) TODO, not implemented yet
        chunk = self.mm[self.keys['|CC1'][id]['start'] : self.keys['|CC1'][id]['end']]
        dwIndexChannel = mapData(chunk, 4, 'UINT32')
        dx = mapData(chunk, 8, 'DBL')
        x0 = mapData(chunk, 16, 'DBL')
        dwIndexGroup = mapData(chunk, 24, 'UINT32')
        dwDefaultChunkBytes = mapData(chunk, 28, 'UINT32')
        flags = mapData(chunk, 32, 'UINT8')
        pretriggerUse = mapData(chunk, 33, 'UINT8')
        componentCombination = mapData(chunk, 34, 'UINT8')
        lenStrXUnit = mapData(chunk, 36, 'UINT16')
        strXUnit = mapData(chunk, 38, 'STR', strLen=lenStrXUnit)

        numComponents = 1
        if componentCombination in COMPONENTCOMBINATION_2COMPONENTS:
            numComponents = 2

        # now take first |CM1 
        chunk = self.mm[self.keys['|CM1'][id + cm_offset]['start'] : self.keys['|CM1'][id + cm_offset]['end']]
        numericalFormat1 = mapData(chunk, 4, 'UINT8')
        additionalSpecifier1 = mapData(chunk, 5, 'UINT8')
        scaleFactor1 = mapData(chunk, 8, 'DBL')
        scaleOffset1 = mapData(chunk, 16, 'DBL')
        lenStrUnit1 = mapData(chunk, 24, 'UINT16')
        strUnit1 = mapData(chunk, 26, 'STR', strLen=lenStrUnit1)
        
        # now take second |CM1 if needed
        if numComponents == 2:
            chunk = self.mm[self.keys['|CM1'][id + cm_offset + 1]['start'] : self.keys['|CM1'][id + cm_offset + 1]['end']]
            numericalFormat2 = mapData(chunk, 4, 'UINT8')
            additionalSpecifier2 = mapData(chunk, 5, 'UINT8')
            scaleFactor2 = mapData(chunk, 8, 'DBL')
            scaleOffset2 = mapData(chunk, 16, 'DBL')
            lenStrUnit2 = mapData(chunk, 24, 'UINT16')
            strUnit2 = mapData(chunk, 26, 'STR', strLen=lenStrUnit2)
        else:
            numericalFormat2 = 0
            additionalSpecifier2 = 0
            scaleFactor2 = 0
            scaleOffset2 = 0
            lenStrUnit2 = 0
            strUnit2 = ''

        # now take |CH1
        chunk = self.mm[self.keys['|CH1'][id]['start'] : self.keys['|CH1'][id]['end']]
        dwEnvelopeReduction = mapData(chunk, 4, 'UINT32')
        triggertime = mapData(chunk, 8, 'DBL')
        uEffectiveLengBytes = mapData(chunk, 16, 'UINT64')
        uChunkBytes = mapData(chunk, 24, 'UINT64')
        uEnvelopeBytes = mapData(chunk, 32, 'UINT64')

        if uEffectiveLengBytes != uChunkBytes:
            raise IMC3Error('uEffectiveLengBytes != uChunkBytes. Events are not implemented!')
        
        # now take |CN1
        chunk = self.mm[self.keys['|CN1'][id]['start'] : self.keys['|CN1'][id]['end']]
        indexBit = mapData(chunk, 4, 'UINT8')
        tmp = 5
        lenStrName = mapData(chunk, tmp, 'UINT16')
        strName = mapData(chunk, tmp + 2, 'STR', strLen=lenStrName)
        tmp = tmp + lenStrName
        lenStrComment = mapData(chunk, tmp, 'UINT16')
        strComment = mapData(chunk, tmp + 2, 'STR', strLen=lenStrComment)
        
        if dwIndexGroup != 0:
            strName = self.get_group_by_id(dwIndexGroup).name + ':' + strName

        # get numrical formats
        cmpFormat1 = NUMERICAL_FORMATS[numericalFormat1]
        if numComponents == 2:
            cmpFormat2 = NUMERICAL_FORMATS[numericalFormat2]

        # get number of values
        bytesPerValue = cmpFormat1['bytes']
        if numComponents == 2:
            bytesPerValue = bytesPerValue + cmpFormat2['bytes']

        if uChunkBytes % bytesPerValue != 0:
            raise IMC3Error('Reading channel has left-over bytes.')
        
        numValues = int(uChunkBytes / bytesPerValue)

        # get data from raw bytes
        # 1) samples component 1
        # 2) samples component 2 (optional)
        # 3) envelope (not implemented)
        # 4) events (not implemented)
        offset  = self.rawOffset

        # vectorized reads with numpy
        raw = np.frombuffer(self.mm, dtype=cmpFormat1['npformat'], count=numValues, offset=offset)
        samples1 = raw * scaleFactor1 + scaleOffset1
        offset += numValues * cmpFormat1['bytes']

        if numComponents == 2:
            # vectorized reads with numpy
            raw = np.frombuffer(self.mm, dtype=cmpFormat2['npformat'], count=numValues, offset=offset)
            samples2 = raw * scaleFactor2 + scaleOffset2
            offset += numValues * cmpFormat2['bytes']
        else:
            samples2 = []

        # skip envelope information in data
        self.rawOffset = offset + uEnvelopeBytes

        return IMC3Channel(
            # from |CC1 key
            dwIndexChannel = dwIndexChannel,
            dx = dx,
            x0 = x0,
            group_id = dwIndexGroup,
            dwDefaultChunkBytes = dwDefaultChunkBytes,
            flags = flags,
            pretriggerUse = pretriggerUse,
            componentCombination = componentCombination,
            xUnit = strXUnit,
            numComponents = numComponents,
            name = strName,
            comment = strComment,
            dwEnvelopeReduction = dwEnvelopeReduction,
            triggertime = triggertime,
            uEffectiveLengBytes =uEffectiveLengBytes,
            uChunkBytes = uChunkBytes,
            uEnvelopeBytes = uEnvelopeBytes,

            # first component
            cmp1numericalFormat = numericalFormat1,
            cmp1additionalSpecifier = additionalSpecifier1,
            cmp1scaleFactor = scaleFactor1,
            cmp1scaleOffset = scaleOffset1,
            cmp1Unit = strUnit1,
            cmp1Values = samples1,
            cmp1Count = len(samples1),

            # second component
            cmp2numericalFormat = numericalFormat2,
            cmp2additionalSpecifier = additionalSpecifier2,
            cmp2scaleFactor = scaleFactor2,
            cmp2scaleOffset = scaleOffset2,
            cmp2Unit = strUnit2,
            cmp2Values = samples2,
            cmp2Count = len(samples2)
        )

    def _read_groups(self):
        out = dict()
        for i in range(self.header.dwCountGroups):
            group = self._parse_group(i)
            
            # save in dict
            if group.name in out.keys():
                # name is already taken as single value
                raise IMC3Error('Group has a duplicate name.')

            out[group.name] = group

        return out

    def _read_single_values(self):
        out = dict()
        for i in range(self.header.dwCountSingleValues):
            singleValue = self._parse_single_value(i)

            # save in dict
            if singleValue.name in out.keys():
                # name is already taken as single value
                raise IMC3Error('Single value has a duplicate name.')

            out[singleValue.name] = singleValue
            
        return out

    def _read_text_variables(self):
        out = dict()
        
        if '|Ct1' in self.keys.keys():
            for i in range(len(self.keys['|Ct1'])):
                textVariable = self._parse_single_text_variable(i)

                # save in dict
                if textVariable.name in out.keys():
                    # name is already taken as single value
                    raise IMC3Error('Text variable has a duplicate name.')

                out[textVariable.name] = textVariable
            
        return out

    def _read_text_arrays(self):
        out = dict()
        
        if '|CT1' in self.keys.keys():
            for i in range(len(self.keys['|CT1'])):
                textArray = self._parse_single_text_array(i)

                # save in dict
                if textArray.name in out.keys():
                    # name is already taken as single value
                    raise IMC3Error('Text variable has a duplicate name.')

                out[textArray.name] = textArray
            
        return out

    def _read_channels(self):
        out = dict()
        cm_offset = 0
        for i in range(self.header.dwCountNamedChannels):
            channel = self._parse_channel(i, cm_offset)

            # save in dict
            if channel.name in out.keys():
                # name is already taken as single value
                raise IMC3Error('Text variable has a duplicate name.')

            out[channel.name] = channel
            
        return out
    
    def _validate(self):
        # checks magics at end of file
        chunk = self.mm[self.keys['|CJ1'][0]['start'] : self.keys['|CJ1'][0]['end']]

        if self.header.dwMagic1 != mapData(chunk, 4, 'UINT32'):
            raise IMC3Error('dwMagic1 not matching in start and end of file.')
        
        if self.header.dwMagic2 != mapData(chunk, 16, 'UINT32'):
            raise IMC3Error('dwMagic2 not matching in start and end of file.')

    def list_groups(self, name='*'):
        # list all groups by name
        out = list()

        for k, v in self.groups.items():
            out.append(v.name)

        return fnmatch.filter(out, name)

    def get_group_by_name(self, name):
        for k, v in self.groups.items():
            if v.name == name:
                return v
        
    def get_group_by_id(self, id):
        for k, v in self.groups.items():
            if v.id == id:
                return v
            
    def list_variables(self, name='*', type='*', group='*'):
        # list all variables by name
        out = list()

        if group != '*':
            if group not in self.list_groups():
                group = -1
            else:
                group = self.get_group_by_name(group).id
        else:
            group = -1

        if type in ['*', 'channel']:
            for k, v in self.channels.items():
                if fnmatch.fnmatch(v.name, name) and group in [-1, v.group_id]:
                    out.append((v.name, 'channel'))

        if type in ['*', 'single value']:
            for k, v in self.singleValues.items():
                if fnmatch.fnmatch(v.name, name) and group in [-1, v.group_id]:
                    out.append((v.name, 'single value'))

        if type in ['*', 'text variable']:
            for k, v in self.textVariables.items():
                if fnmatch.fnmatch(v.name, name) and group in [-1, v.group_id]:
                    out.append((v.name, 'text variable'))

        if type in ['*', 'text array']:
            for k, v in self.textArrays.items():
                if fnmatch.fnmatch(v.name, name) and group in [-1, v.group_id]:
                    out.append((v.name, 'text array'))

        return sorted(out, key = lambda x:x[0])
    
    def get_variable_by_name(self, name):
        # search single values
        for k, v in self.singleValues.items():
            if v.name == name:
                return v
            
        # search text variables
        for k, v in self.textVariables.items():
            if v.name == name:
                return v

        # search text arrays
        for k, v in self.textArrays.items():
            if v.name == name:
                return v
            
        # search channels
        for k, v in self.channels.items():
            if v.name == name:
                return v

    def isVariable(self, name):
        # checks if variable id or name exists
        varnames = [x[0] for x in self.list_variables()]

        if name in varnames:
            return True
        else:
            return False

    def channel_as_df(self, name):
        # returns channel as pd dataframe
        for k, v in self.channels.items():
            if v.name == name:
                break

        # x data
        if v.numComponents == 1:
            # from x0 and dx
            xValues = v.x0 + np.arange(0, v.cmp1Count) * v.dx
        else:
            # from component2
            xValues = v.cmp2Values

        # y data
        yValues = v.cmp1Values

        out = pd.DataFrame({'x': xValues, 'y': yValues})

        return out

def mapSingleValue(data, startIndex, numericalFormat):
    match numericalFormat:
        case 1: # unsinged byte
            return mapData(data, startIndex, 'UINT8')
        case 2: # signed byte
            return mapData(data, startIndex, 'SINT8')
        case 3: # unsigned short
            return mapData(data, startIndex, 'UINT16')
        case 4: # signed short
            return mapData(data, startIndex, 'SINT16')
        case 5: # unsigned long
            return mapData(data, startIndex, 'UINT32')
        case 6: # signed long
            return mapData(data, startIndex, 'SINT32')
        case 7: # float
            return mapData(data, startIndex, 'FLT')
        case 8: # double
            return mapData(data, startIndex, 'DBL')
        case 12: # 8 byte unsigned long
            raise IMC3Error('Single value format "8 byte unsigned long" not defined yet.')
        case 14: # 8 byte signed long
            raise IMC3Error('Single value format "8 byte signed long" not defined yet.')
        case _:
            raise IMC3Error('Invalid format for single value')
    
def mapData(data, start, dtype, *, strLen=None):
    if dtype == "STR":
        raw = data[start: start+strLen]
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("cp1252")

    fmt, size = MAPPING_FORMATS[dtype]
    return struct.unpack(fmt, data[start:start+size])[0]

def isValidKey(input):
    # checks if key is in list VALID_KEYS
    if input in VALID_KEYS:
        return True
    else:
        return False

def isLanguageValid(wCodePage, wLanguage):
    # checks if Language and CodePage settings are matching 
    try:
        validList = VALID_LANGUAGES[wCodePage]
    except:
        raise IMC3Error('Unsupported wCodePage')

    if wLanguage in validList:
        return True
    else:
        return False
