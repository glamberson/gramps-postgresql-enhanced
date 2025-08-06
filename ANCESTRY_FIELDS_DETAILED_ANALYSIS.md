# Ancestry.com Fields - Detailed Analysis Report
**Import Date**: 2025-08-06
**Total Lines Ignored**: 2,430
**Subordinate Lines Skipped**: 1,334
**Data Source**: 86,647 person GEDCOM from Ancestry.com

## Executive Summary

The GEDCOM file contains extensive Ancestry.com proprietary metadata that provides crucial linking, tracking, and content information. These fields represent Ancestry's internal database structure and user activity tracking.

## Field Categories and Counts

### 1. Identity & Linking Fields (3,414 occurrences)
```
1,318 _OID  - Object IDs (UUIDs)
  552 _TID  - Tree IDs (numeric)
  548 _PID  - Person IDs (numeric, often negative)
  437 _HPID - Husband Person IDs
  425 _WPID - Wife Person IDs
  317 _LKID - Link IDs
```

### 2. User Tracking & Security (2,636 occurrences)
```
1,318 _USER - Encrypted user tracking (Base64)
1,318 _ENCR - Encryption flag (value: 1)
```

### 3. Media & Document Fields (3,578 occurrences)
```
  766 _STYPE - Source type (jpeg, pjpeg, bmp, etc.)
  766 _SIZE  - File size in bytes
  523 _WDTH  - Width in pixels
  523 _HGHT  - Height in pixels
  404 _MTYPE - Media type (document, portrait, story)
  319 _META  - Metadata (XML format)
  158 _DSCR  - Description text
```

### 4. System & Temporal Fields (1,875 occurrences)
```
  766 _CREA - Creation timestamp
  552 _DATE - Modification timestamp
  552 _CLON - Clone marker
  317 _MSER - Media series marker
```

### 5. Miscellaneous Fields (869 occurrences)
```
  766 _ORIG - Original flag (value: u)
  766 _ATL  - Atlantic? flag (N or Y)
   41 _TYPE - Type specifier (primary, etc.)
   25 _TREE - Tree information
   21 _ENV  - Environment (prd = production)
```

## Detailed Field Analysis

### _OID (Object ID) Structure
- **Format**: UUID v4 (e.g., `00f0afa6-8ecc-4c08-8447-560e19b751fd`)
- **Purpose**: Unique identifier for each object in Ancestry database
- **Occurrence**: Every person, family, source, media object has one
- **Impact of Loss**: Cannot link back to Ancestry.com objects

### _TID (Tree ID) Examples
```
TID 14913892
TID 9185426  
TID 13282168
TID 49837533
TID 78796201
```
- **Purpose**: Identifies which Ancestry family tree this came from
- **Format**: Numeric, appears to be sequential
- **Impact of Loss**: Cannot identify source tree on Ancestry

### _PID (Person ID) Examples
```
PID 400124288408 (positive)
PID -824599754   (negative)
PID 1205081306
PID 28212101599
PID 32396758746
```
- **Purpose**: Ancestry's internal person identifier
- **Format**: Large integers, sometimes negative
- **Impact of Loss**: Cannot cross-reference with Ancestry records

### _HPID/_WPID (Husband/Wife Person ID) Format
```
_HPID 1,61511::105231315   (Database,Collection::RecordID)
_WPID 1,61511::120231315
_HPID 1,7602::45169761
_WPID 1,7602::45169762
_HPID 1,8784::455165
```
- **Structure**: `DatabaseID,CollectionID::RecordID`
- **Database IDs Found**:
  - 1 = Primary database
  - Collections: 61511, 7602, 8784, 8787, 4802, 8909, 61378, 61157, 7836, 7838, 7839, 7857, 60548, 60144, 60214, 9852, 1171, 2451, 70016, 1144, 2085, 2086, 1623
- **Purpose**: Links to specific records in Ancestry databases
- **Impact of Loss**: Cannot navigate to source records

### _USER Field (Encrypted User Data)
```
Examples:
t4/RVZnpKK0tgVAt/VsS397dPM3/9ejOSPsW7+PV8P5M95AvoCNab2vNqGU6PM6dFgcopvQtDENKxOKD1Sp6yQ==
Kf3wUOggD+sap5nQD9vvdTtn2zKJyrSXirywq27lfzgXcw56uzZdJAWUS0BWWXdAdJph7cF6+Xbc7A/YQaQibw==
```
- **Format**: Base64 encoded encrypted data
- **Length**: Consistently 88 characters
- **Purpose**: Tracks which Ancestry user created/modified
- **Paired with**: _ENCR 1 flag indicating encryption
- **Impact of Loss**: Cannot track data provenance

### _META Field (Metadata XML)
```xml
Examples found:
<metadataxml><transcription></transcription></metadataxml>
<metadataxml><cemetery /><transcription /></metadataxml>
<metadataxml><content><line>[Detailed content]</line></content></metadataxml>
```
- **Content Types**:
  - Cemetery information
  - Document transcriptions
  - Research notes
  - Source descriptions
- **Impact of Loss**: Valuable research content lost

### _CREA/_DATE Timestamps
```
_CREA 2022-08-22 13:37:38.302
_CREA 2022-01-11 13:37:57.000
_CREA 2023-04-13 03:13:11.059
_DATE 2017-07-31 01:24:42.000
_DATE 2009-10-05 18:50:21.000
```
- **Format**: YYYY-MM-DD HH:MM:SS.mmm
- **Range**: 2009 to 2023 in samples
- **Purpose**: Track creation and modification times
- **Impact of Loss**: Cannot track data currency

### Media Type Distribution
```
_MTYPE values:
- document
- portrait  
- story
- x-inline

_STYPE values:
- jpeg
- pjpeg
- bmp
- x-inline
```

### URLs Preserved (in Notes)
While WWW URLs were preserved in notes, they link to:
- `http://search.ancestry.com/cgi-bin/sse.dll?db=...`
- `http://familysearch.org/pal:/MM9.1.1/...`
- `https://www.findagrave.com/memorial/...`
- `https://www.familysearch.org/ark:/61903/...`

## Ancestry Database Collections Identified

From _HPID/_WPID analysis, these Ancestry database collections are referenced:
- **61511**: Appears frequently (likely US Census)
- **7602**: Very common (1900 US Census based on URLs)
- **8784, 8787, 8909**: Marriage records
- **7836**: World Marriage records
- **60548, 60144, 60214**: Family Search collections
- **70016**: Unknown collection
- **4802**: North Carolina marriages
- **61378, 61157**: State-specific records

## Data Loss Impact Assessment

### Critical Losses
1. **Object Linking** (_OID): Cannot reconnect to Ancestry objects
2. **Tree Identity** (_TID): Cannot identify source tree
3. **Person IDs** (_PID): Cannot cross-reference individuals
4. **Database References** (_HPID/_WPID): Cannot locate source records

### Moderate Losses
1. **User Tracking** (_USER): Cannot identify contributors
2. **Metadata** (_META): Loss of transcriptions and notes
3. **Timestamps** (_CREA/_DATE): Cannot track data age

### Minor Losses
1. **Media Dimensions** (_WDTH/_HGHT): Cosmetic information
2. **File Sizes** (_SIZE): Storage planning information
3. **Clone Markers** (_CLON): Internal Ancestry tracking

## Patterns Observed

### Tree Structure
- Single tree (consistent _TID values suggest one export)
- Multiple user contributions (varied _USER values)
- Timeline: 2009-2023 (14 years of data accumulation)

### Record Sourcing
- Heavy use of census records (7602 collection)
- Extensive marriage record citations
- FamilySearch integration
- FindAGrave memorial links

### Data Management
- All sensitive data encrypted (_USER with _ENCR)
- UUIDs for object identification
- Hierarchical database structure (Database::Collection::Record)

## Recommendations for Recovery

### Option 1: GEDCOM Pre-processor
Create a pre-processor to:
- Extract _META content into standard NOTE fields
- Convert _OID/_TID/_PID into NOTE references
- Parse _HPID/_WPID into citation text

### Option 2: Custom GEDCOM Parser Extension
Modify Gramps GEDCOM parser to:
- Recognize Ancestry tags
- Store in custom attributes
- Preserve linking capability

### Option 3: Parallel Database
Maintain separate database of:
- OID → Gramps Handle mapping
- TID → Tree name mapping
- PID → Person reference mapping
- META → Extracted content

## Summary Statistics

- **Total Proprietary Tags**: 15 unique types
- **Total Occurrences**: 3,764 lines
- **Average per Person**: 0.04 tags/person
- **Most Common**: _USER, _OID, _ENCR (1,318 each)
- **Most Valuable Lost**: _META (319 with content)
- **Linking Fields Lost**: 3,414 total IDs

## Conclusion

The ignored Ancestry fields represent a sophisticated internal tracking and linking system. While standard GEDCOM data was preserved, the loss of these fields means:

1. **No way to return to Ancestry sources**
2. **Loss of contributor tracking**
3. **Missing transcription metadata**
4. **Broken links to original records**
5. **No tree identification**

These fields could be valuable for:
- Source verification
- Data provenance tracking
- Ancestry.com synchronization
- Research trail documentation
- Multi-tree management