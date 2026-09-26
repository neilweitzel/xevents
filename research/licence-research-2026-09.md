# Licence research: xevents candidate sources

**Session dates:** 2026-09-25 to 2026-09-26 (UTC).

Every quote below was read from the linked page during this session, either
by fetching it or, where marked "(search excerpt)", from the search
index's copy of that page. Where a page could not be read, or its terms say nothing, the entry says so. Nothing
is filled in from general knowledge. Registry names are in backticks. The
recorded reading and the resulting right for each source are in
[`config/source-registry.json`](../config/source-registry.json). The policy is
in [ADR 0030](../docs/adr/0030-source-licence-registry.md).

**How to read this document.**

- The public dataset is CC BY 4.0, so a source may `publish` only if its
  terms are compatible with that: not non-commercial, not share-alike, and
  not re-published from somewhere else.
- A publisher that says nothing about reuse has granted nothing in writing.
  xevents may still publish on that reading, but it records the source as
  `explicit_grant: false`.
- This is a record of what publishers say. It is not legal advice.

---

## Leak-site claim trackers

**`ransomlook_api`**: CC BY 4.0, explicit. Maintainer comment,
[RansomLook issue #590](https://github.com/RansomLook/RansomLook/issues/590#issuecomment-3195206965):

> All content provided by ransomlook.io, including the website, API responses, and datasets, is made available under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
>
> You are free to share and adapt the material for any purpose, even commercially, provided that appropriate credit is given.

The same text is in the [RansomLook README](https://github.com/RansomLook/RansomLook). The platform code is AGPL-3.0. That applies to the code, not the data.

**`ransomfeed_api`**: prose, no named data licence.
[Ransomfeed RSS page](https://ransomfeed.it/index.php?page=rss), in Italian with our translation:

> Il loro utilizzo è sempre libero e aperto a tutti.
> (Their use is always free and open to everyone.)
>
> È inoltre possibile integrare questi feed RSS in qualsiasi piattaforma, anche commerciale, qualora necessario per aumentare il livello di rilevamento in Threat Intelligence.
> (These RSS feeds can also be integrated into any platform, including commercial ones, where needed to raise the level of detection in threat intelligence.)

The [Q1 2024 report](https://ransomfeed.it/data/reports/2024/DRM-Report-Q1-2024-%5BENG%5D.pdf) says (search excerpt): "The total or partial reproduction of this report is free and not intended for commercial use, provided the source is cited as per Creative Commons Attribution • CC BY-NC."

**Reading:** the NC notice covers the PDF reports. The feed and API statements are permissive prose. So the source is `publish`, `explicit_grant: false`, credited. The public API is documented at [api.ransomfeed.it/docs/html](https://api.ransomfeed.it/docs/html). The OpenCTI connector is GPLv3; that is code, not data.

**`threatcluster_first_party`** and **`threatcluster_imported`**:
[ThreatCluster datasets](https://threatcluster.io/datasets):

> Yes. Everything is CC BY 4.0: share and adapt it, including commercially, as long as you credit ThreatCluster and say if you changed it.
>
> Source articles are third-party copyright.

[Ransomware-Intel README](https://raw.githubusercontent.com/Jam0k/Ransomware-Intel/main/README.md):

> a growing share of it is read directly off the leak sites by our own crawler, not imported from an aggregator. Those rows are marked `first_party=yes` and have no equivalent elsewhere.

**Reading:** the README reports 1,317 first-hand rows out of 9,444 over 365 days. Those first-hand rows are a candidate independent class. The imported rows repeat other aggregators, so they are `excluded` (ADR 0030 item 4).

**`ransomwatch_archive`**: The Unlicense. The GitHub licence metadata for [joshhighet/ransomwatch](https://github.com/joshhighet/ransomwatch) reports `Unlicense`. Frozen archive.

**`ransomware_live`**: [ransomware.live T&C](https://www.ransomware.live/t&c):

> The Data is freely available for non-commercial use.
>
> These restrictions apply without prior written approval from the owner of Ransomware.live; exceptions may be granted at the owner's sole discretion.

It stays excluded by ADR 0002.

**`ecrime_ch`**: paid; commercial re-use only on a custom tier ([landscape §1.6](landscape-report.md)). Not re-fetched in this session.

---

## Regulators and official disclosures

**`sec_edgar`** and **`sec_submissions_sic`**: [SEC privacy and copyright statement](https://www.sec.gov/privacy):

> Information presented on sec.gov is considered public information and may be copied or further distributed by users of the web site without the SEC's permission.
>
> Please consider appropriate citation to the SEC as the source.
>
> Please do not use the SEC seal or any of the other logos or artwork from this site.

**US federal works in general**: `hhs_ocr_breach_portal`, `nppes_npi_registry`, `nces_ccd`, `irs_eo_bmf`, `fdic_bankfind`, `ncua_credit_unions`. The pages we read (HHS web policies, NPPES downloads, FDIC API docs, IRS privacy policy) state no reuse terms. The status comes from the statute, [17 U.S.C. § 105](https://www.law.cornell.edu/uscode/text/17/105):

> (a) In General.— Copyright protection under this title is not available for any work of the United States Government

The HHS copyright page returned Access Denied. We did not read the NCUA or NCES terms pages.

**`cisa_kev`**: CC0 1.0. [KEV licence file](https://www.cisa.gov/sites/default/files/licenses/kev/license.txt):

> The KEV database is distributed under the Creative Commons 0 1.0 License. You may use this data in any legal manner but note that information provided at any 3rd party links included in the KEV database are bound by the policies and licenses of those 3rd party websites. Use of the information does not authorize you to use the CISA Logo or DHS Seal

**`wa_ag_breach_notifications`**: no licence stated. The Socrata metadata for [dataset sb4j-ca4h](https://data.wa.gov/Consumer-Protection/Data-Breach-Notifications-Affecting-Washington-Res/sb4j-ca4h) has `license: null`, `provenance: "official"` and `attribution: "Washington State Attorney General's Office Consumer Protection Division"`. The data.wa.gov terms-of-use page returned an error, and the AG page blocked our reader.

**`de_ag_breach_database`**: no licence stated. The Socrata metadata for [dataset dir6-wx8v](https://data.delaware.gov/Public-Safety/Data-Security-Breach-Database/dir6-wx8v) has `license: null`, `attribution: null` and `provenance: "official"`.

**`ca_ag_breach_list`**: no licence stated. The [list page](https://oag.ca.gov/privacy/databreach/list) offers a full CSV but no reuse terms, and `oag.ca.gov/conditions-of-use` returned "Page not found".

**`tx_ag_breach_reports`**: no licence stated for the list. The [Texas OAG site policies](https://www.texasattorneygeneral.gov/site-policies) cover only the office's own use of intellectual property and social media.

**`ia_ag_breach_notifications`**, **`mt_doj_breach_list`**, **`vt_ag_breach_notices`**, **`in_ag_breach_reports`**: no reuse terms found on the list pages:

- [Iowa 2026 list](https://www.iowaattorneygeneral.gov/for-consumers/security-breach-notifications/2026-security-breach-notification) (search excerpt; the direct fetch was blocked by robots rules);
- [Montana list](https://dojmt.gov/office-of-consumer-protection/reported-data-breaches/);
- [Vermont list](https://ago.vermont.gov/categories/security-breach-notices);
- [Indiana index](https://www.in.gov/attorneygeneral/consumer-protection-division/id-theft-prevention/security-breaches/).

---

## Courts, catalogs and curated datasets

**`courtlistener`**: [CourtListener terms](https://wiki.free.law/c/terms/courtlistener/courtlistenercom-terms-of-service-and-policies):

> You acknowledge that while judicial opinions, motions, and other filings are generally in the public domain, other court filings may contain third-party copyrighted works, such as books and articles, that may retain copyright protection.
>
> If you republish or display our data, do not present it in a way that suggests Free Law Project produced, endorsed, or verified an AI-generated analysis of it.

The default API limit is 5 requests per minute, 50 per hour and 125 per day ([REST API help](https://www.courtlistener.com/help/api/rest/)).

**`hibp_breach_catalog`**: CC BY 4.0. [HIBP API v3](https://haveibeenpwned.com/API/v3):

> This work is licensed under a Creative Commons Attribution 4.0 International License.

The same page lists "Misrepresenting the source of the data as originating from somewhere other than Have I Been Pwned" and "Not adhering to the Creative Commons Attribution License" as unacceptable uses.

**`vcdb`**: CC BY-SA 4.0. The [VCDB repository](https://github.com/vz-risk/VCDB) `LICENSE.txt` begins:

> Creative Commons Attribution-ShareAlike 4.0 International Public License

GitHub reports `NOASSERTION` because it does not detect the file. Because of ShareAlike, VCDB cannot flow into the CC BY 4.0 output, so it is corroboration and validation only.

**`cissm_cyber_events`**: not retrieved. The CISSM database page returned an error to our reader. The [UMD GoTech page](https://gotech.umd.edu/cyber-events-database) describes the database but states no reuse terms.

**`eurepoc`**: not stated. The [EuRepoC database page](https://eurepoc.eu/database/) offers downloads and states no licence.

**`threatcluster_incident_clusters`**: CC BY 4.0 (see above). The summaries are model-generated, and "Source articles are third-party copyright."

**`hackmageddon`**: [HACKMAGEDDON about page](https://www.hackmageddon.com/about/):

> If you use HACKMAGEDDON data in research, reporting, or presentations, attribution is appreciated.

**`privacy_rights_clearinghouse`**: the [PRC terms page](https://privacyrights.org/terms-use) footer reads:

> Except where otherwise noted, content on this website is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license

The full chronology database is sold separately ([Data Breach Chronology store](https://store.databreachchronology.org/)).

---

## Entity and sector directories (enrichment only)

**`gleif_lei`**: [GLEIF terms](https://www.gleif.org/en/meta/lei-data-terms-of-use):

> The data available through the Access Service are provided under the CC0 licence

**`wikidata`**: [Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing):

> All structured data (i.e. the main, Property, Lexeme, and EntitySchema namespaces) is released into the public domain under Creative Commons Zero.

**`opensanctions`**: the [OpenSanctions repository](https://github.com/opensanctions/opensanctions) says (search excerpt):

> Data files produced by OpenSanctions are licensed under CC BY-NC 4.0

Commercial use requires a data licence ([bulk data docs](https://www.opensanctions.org/docs/bulk/), search excerpt). Excluded; not needed.
