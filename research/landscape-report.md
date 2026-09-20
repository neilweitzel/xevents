# xevents — Landscape Research Report

**Date:** September 17, 2026
**Purpose:** Validate feasibility, map the competitive/data landscape, and identify what's usable today for xevents — an evidence-first incident-intelligence application that records, preserves, and reconciles *public* claims about cyber incidents (starting with ransomware victim listings and breach disclosures). Design thesis: never treat a single source's claim as unquestioned fact; store each observation with source, timestamp, entity details, supporting evidence, confidence, and correction history; resolve multiple observations into cautious, explainable incident records; long-term, a public research surface for trend analysis.

**Method:** Six parallel research workers, text search + page fetch only (no live browser). Every factual claim below carries a source URL. Items that could not be verified are flagged **UNVERIFIED**.

**Classification key:** FREELY USABLE = public, no key/payment, machine access documented or trivial. PAID = commercial tier required. RESTRICTED = key-gated, ToS-limited, offline, or scrape-only-with-friction.

---

## 1. Ransomware Victim Listing Sources

### 1.1 RansomLook (ransomlook.io) — FREELY USABLE (best open ingest)

- **Exposes:** Victim posts scraped from data-leak sites: `post_title` (victim name), `group_name`, `discovered` (UTC, no timezone), free-text `description`, `link`, `magnet`, `screen` (screenshot), `private` flag, `misp_uuid`. Plus group profiles (affiliates, contacts, PGP keys, wallets, ransom notes), threat actors, markets. **No country or sector fields** — sector sometimes appears inside free-text `description` only.
- **API/bulk:** `https://www.ransomlook.io/api` — no key for public endpoints (optional `RANSOMLOOK_API_KEY`; only `/api/export/{db}` requires auth). Endpoints: `/api/posts/period/{start}/{end}`, `/api/last/{days}`, `/api/recent/{n}`, `/api/group/{name}`, `/api/search`. Docs: `https://www.ransomlook.io/doc/`. Full platform is open source (GitHub RansomLook/RansomLook), actively maintained (README updated Sep 2026).
- **Cadence/coverage:** Operators recommend cron scrape+parse every 2 hours. v1.9.0 release notes claim 2,000 onion sites monitored (from ~2025; current count UNVERIFIED).
- **Licensing:** **All content from ransomlook.io — website, API responses, datasets — is CC BY 4.0**: free to share and adapt for any purpose, even commercially, with attribution. Maintainers confirmed in writing (issue #590). Software is separately AGPL-3.0.
- **Sources:** https://github.com/RansomLook/RansomLook/blob/main/README.md · https://github.com/ransomlook/ransomlook/issues/590 · https://github.com/fbicyber/opencti__connectors/blob/HEAD/external-import/ransomlook/README.md

### 1.2 ransomfeed.it — FREELY USABLE (second-best; clearest commercial-reuse terms)

- **Exposes:** Victim listings (title, detection date, group) in two RSS tiers: *immediato* (raw scrape, onion sites scanned **every 60 minutes**) and *completo* (analyst-moderated, primarily victim **country**, ~6h after detection).
- **API/bulk:** Public APIs with self-serve filters, JSON output (exact endpoints UNVERIFIED); RSS feeds; official OpenCTI connector converts claims to STIX 2.1.
- **Licensing:** "Il loro utilizzo è sempre libero e aperto a tutti" — **usage always free and open to all, including integration into commercial platforms.** No key.
- **Sources:** https://ransomfeed.it/index.php?page=rss · https://github.com/ransomfeed/Ransomfeed_OpenCTI_connector

### 1.3 ransomware.live — RESTRICTED (richest free metadata, but terms-limited)

- **Exposes:** Richest enrichment of the free options: `victim, group, discovered, attackdate, country, activity, domain, data_size, description, claim_url, url, press, ransom, screenshot, infostealer`, plus sector victims, CERT contacts, YARA rules, press coverage, SEC 8-K filings. **PRO tier** (free key via email, 500k calls/month) adds ransom notes, negotiation transcripts, IOCs, combined-filter search, undelayed victims.
- **API:** Base `https://api.ransomware.live/v2` (v1 deprecated) — **free, no auth, ~1 req/min per endpoint** (rate limit from third-party docs; UNVERIFIED from primary docs).
- **Cadence/coverage:** `/v2/info` reported 393 groups / 31,303 victims as of 2026-08-29. **Free v2 victims are deliberately delayed vs PRO.**
- **Licensing:** v2 is **"Personal use only … not intended for corporate or business use."** T&C (fetched 2026-09-17) expressly: §4 prohibits "Redistribution as an API" and "Raw data publishing" (API, file, or otherwise); §5 commercial use strictly prohibited without prior written approval; §7 no warranty ("inclusion … does not constitute a determination or confirmation … that a claimed event occurred"); §9 formal removal/dispute process (discretionary); §12 French law jurisdiction. **xevents cannot re-serve its dataset without written permission.**
- **Sources:** http://www.ransomware.live/api · http://ransomware.live/t&c · https://github.com/jmousqueton/ransomware.live

### 1.4 ransomwatch (joshhighet) — FREELY USABLE (historical only; dead as a live feed)

- **Status:** Repo archived 2026-03-03; collection stopped 2025-06-16; live endpoints dead. Frozen dataset fetchable: **16,072 claims across 157 groups, 2020-01-12 → 2025-06-16** (raw.githubusercontent.com). License: Unlicense (public domain). Useful only as a historical baseline; ransomware.live was originally its fork.
- **Sources:** https://github.com/joshhighet/ransomwatch · https://github.com/valitino/osintoolkit/blob/HEAD/12-darkweb/leak-monitoring/ransomware-live.md

### 1.5 DarkFeed (darkfeed.io) — PAID

- **Exposes:** 17,605 all-time events across 246 groups / 113 countries (per site, Sep 2026); sector breakdowns, heat maps, monthly flows, live victim ticker; API V3 deployed Dec 2025. Limited free dashboard; full dataset/API gated behind commercial subscription (pricing unpublished, UNVERIFIED). ⚠️ Name collision: Cybersixgill's "Darkfeed" is a different product (dark-web IOC blacklist, not victim listings).
- **Sources:** https://darkfeed.io/get-started/ · https://darkfeed.io/groups-timeline/

### 1.6 ecrime.ch — PAID

- **Exposes:** Extortion-exposure monitoring: leak-site records, actor profiles, claim screenshots, news, analyst notes, chat records, vulnerability/KEV entries; investigative search with actor/country/sector filters; weekly trend reports. Explicitly caveats that observed events "reflect monitored leak-site and extortion activity, **not independent confirmation** of every intrusion" — aligns with xevents' evidence-first stance.
- **API/bulk:** Dashboard + API and JSON/CSV export on **Professional tier: USD 2,799/year**. **Commercial tier (custom pricing)** explicitly includes "Commercial re-use of data" — the tier xevents would need for republication.
- **Sources:** http://ecrime.ch · https://ecrime.ch/help/search/investigative-search/

### 1.7 deepdarkCTI (fastfire/deepdarkCTI, GitHub) — FREELY USABLE (directory, not data)

- Curated directory of dark-web CTI sources (gang onion domains, forums, Telegram channels) — useful for building your own Tor scraper, not as victim data. Maintained (README updated ~Sep 2026).
- **Source:** https://github.com/fastfire/deepdarkCTI

### 1.8 Coverage gaps — what NO aggregator provides

1. **Claim verification.** All track claims made by attackers, not confirmed breaches. No aggregator publishes a claim-confidence or retraction feed.
2. **Compromise-to-disclosure lag.** `discovered` = listing-seen date, not intrusion date. ransomware.live's `attackdate` is frequently empty.
3. **Consistent country/sector enrichment.** RansomLook (best license) has neither field; ransomfeed.it adds country with ~6h analyst delay; ransomware.live has both but completeness UNVERIFIED.
4. **De-listing/removal events.** Groups remove victims who pay; no aggregator publishes a structured "listing removed" history.
5. **Non-Tor extortion channels.** Scrapers target onion DLS sites; Telegram/clearweb/forum extortion (growing since 2024–25) is under-covered except by paid tiers.
6. **Ransom amounts/negotiation transcripts/wallets** are mostly gated (ransomware.live PRO, RansomLook group profiles).
7. **Seizure/takedown blind spots.** When a group's site is seized or goes dark, scrapers go silent — absence must be read as "not observed," never "inactive."

---

## 2. Breach Disclosure Sources

### 2.1 SEC EDGAR — 8-K Item 1.05 cybersecurity filings — FREELY USABLE

- **Regulatory context:** Item 1.05 adopted July 2023, effective Dec 18, 2023. Requires disclosure of any cybersecurity incident the registrant *determines to be material* — nature, scope, timing, and material impact — **generally within four business days of the materiality determination** (not of discovery). AG of the U.S. can delay for national-security reasons. Foreign private issuers disclose comparably on Form 6-K.
- **Practice note (important):** SEC staff clarified (May 2024) that Item 1.05 is **not for voluntary disclosure** — immaterial/not-yet-assessed incidents go under Item 8.01 instead. Filings visibly shifted: 2024 saw 26 Item 1.05 filers (17 before, 9 after the guidance) while Item 8.01 cyber disclosures jumped from 6 to 28. A 2025 joint petition asked the SEC to rescind the requirement (citing confusion/defensive filings). UNVERIFIED: 2025–2026 Item 1.05 totals beyond Feb-2025 snapshots; volume appears to be in the dozens per year.
- **Access (all free, U.S. public domain data):**
  - `data.sec.gov` JSON APIs: `https://data.sec.gov/submissions/CIK{cik10}.json` (filing history), `https://www.sec.gov/files/company_tickers.json` (ticker→CIK). Filing documents at `https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/{primaryDocument}`.
  - **efts.sec.gov full-text search JSON**: `GET https://efts.sec.gov/LATEST/search-index?q=…&forms=8-K&dateRange=custom&startdt=…&enddt=…` — boolean operators, ~100 hits/page, 10,000-result window. **Limitation: filters on root form (8-K), not on 8-K *item*** — isolating Item 1.05 requires text search ("Item 1.05") within 8-K results. Full-text index covers ~4 years.
  - **Bulk:** `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` (~1.56 GB, nightly ~3:00 AM ET); quarterly `full-index/{YYYY}/QTR{n}/master.idx`.
- **Rate limits:** **10 requests/second** per IP/project; every programmatic request must send a descriptive `User-Agent` with contact info (missing/generic UAs get 403).
- **xevents caveats:** No structured "Item 1.05" field — item filtering is text-search only; 8-K/A amendments and voluntary Item 8.01 filings must be linked manually; the 4-day clock runs from the unobservable internal materiality determination, so compromise-to-disclosure lag can't be computed from EDGAR alone.
- **Sources:** https://www.sec.gov/newsroom/press-releases/2023-139 · https://www.sec.gov/newsroom/whats-new/gerding-cybersecurity-incidents-05212024 · https://www.SEC.GOV/about/webmaster-frequently-asked-questions · https://www.debevoise.com/-/media/files/insights/publications/2025/02/lessons-learned-one-year-of-form-8k-material.pdf

### 2.2 State attorneys-general breach notification databases

- **California AG — FREELY USABLE:** https://oag.ca.gov/ecrime/databreach/list — searchable by org name and breach-date range; columns: Organization Name, Date(s) of Breach, Reported Date; "Download Full Data Breach List (CSV)" link (exact href UNVERIFIED); per-record "Sample Notification" PDFs. Threshold: >500 California residents. Coverage back to 2012; current (entries dated 09/15/2026 visible at research time). The rich submitted fields (breach type, counts) are **not** published — only the consumer sample-letter PDF.
- **Washington AG — FREELY USABLE:** Two actively updated Socrata datasets on data.wa.gov — `sb4j-ca4h` (breach notifications; JSON/XML/CSV exports + SoQL API) and `padd-mby7` (personal-information breakdown per notice). Threshold: >500 Washington residents, notice within 30 days of discovery. Also runs a daily "Data Breach Live Statistics" page and an annual Data Breach Report.
- **Maine AG — RESTRICTED (offline):** Taken offline **June 12, 2026** after two fabricated filings (impersonating VRChat — 2.4M claimed — and Discord — 10M claimed) were submitted by a third party. **Hoax injection into public registers is a demonstrated, current threat — directly supports xevents' evidence-first design.**
- **Texas AG — RESTRICTED (practical):** Scrape-only, stateful transient request tokens, brittle.
- **Other states:** ~15 states publish at all (VT, MA, IN, NC, CT, MO, VA, FL, etc.); most are ad-hoc HTML lists with no API, inconsistent fields/thresholds/cadence. Per-state currency UNVERIFIED beyond CA/WA/ME/TX/MA/VT. **No multi-state machine-readable aggregator exists.** Closest: open-source **Breach Gazette** (https://github.com/slicedearth/breachgazette) — a provenance-first observatory covering WA/CA/MA + non-US sources; a reference implementation, not a data API.
- **Sources:** https://oag.ca.gov/ecrime/databreach/list · https://data.wa.gov/d/sb4j-ca4h · https://www.maine.gov/ag/news-and-library/press-releases/statement-office-maine-attorney-general-abuse-data-breach-reporting · https://github.com/slicedearth/breachgazette

### 2.3 HHS OCR breach portal ("wall of shame") — FREELY USABLE data, SCRAPE-ONLY access

- Public records of HIPAA breaches affecting **500+ individuals**, 2009–present: entity name, state, individuals affected, dates, breach type. Portal: https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf. **No official API or bulk download** — programmatic access is scraping the JSF portal (one community scraper does the full archive in ~70 requests / ~140s: https://github.com/aarondutton-grc/hhs-hipaa-breach-scraper); a manual CSV-export icon yields a fuller `web_description` field. **Coverage caveat:** healthcare/HIPAA entities only, and ransomware is systematically under-represented (entities invoke the "low probability of compromise" assessment to avoid reporting).
- **Sources:** https://www.fiercehealthcare.com/regulatory/ocr-rolls-out-modifications-to-its-hipaa-breach-reporting-site · https://www.fiercehealthcare.com/privacy-security/health-systems-use-ocr-loophole-to-forgo-breach-reporting-following-a-ransomware

### 2.4 Other public company-disclosure channels — mostly SCRAPE-ONLY

- **Company press releases / security pages / trust centers / IR pages:** No central feed; many incidents are disclosed first on company newsrooms. Fragmented, per-company scraping.
- **Stock exchanges:** NYSE/Nasdaq require prompt public disclosure of material news via press release (Reg FD), but the exchange is only *notified* — **no exchange incident-notice feed exists.**
- **10-K Item 106 (Reg S-K Item 106 / 10-K Item 1C)** cybersecurity disclosures: FREELY USABLE via EDGAR (same access as 8-K) — context for an incident record, not incident-level data.

---

## 3. Existing Tools and Gaps

### 3.1 Tools surveyed

| Tool | Type | Classification |
|---|---|---|
| **MISP** (CIRCL) | General threat-intel platform; Event→Attribute/Object model, taxonomies, Galaxies, sightings, decay models; STIX import/export | FREELY USABLE (AGPL-3.0, self-host) |
| **OpenCTI** (Filigran) | STIX 2.1 knowledge-graph CTI platform; 100+ connectors incl. ransomlook | FREELY USABLE (Community Edition, Apache 2.0) / PAID (Enterprise/SaaS) |
| **DataBreaches.net** | One-person investigative breach journalism since 2009; editorial, no schema or API | FREELY USABLE (reading source only) |
| **Have I Been Pwned** | Curated verified breach catalog (`/api/v3/breaches` keyless, **CC BY 4.0**); account lookups keyed/paid | FREELY USABLE (catalog) / PAID (account API) |
| **CIRCL** | Open-source IR tooling + free feeds: AIL Framework (AGPL; crawls Tor/paste sites, indexes leaks), cve-search, live MISP OSINT feed (no auth, ~hourly) | FREELY USABLE |
| **ransomware.live** | Victim-claim tracker + free v2 API + keyed PRO API | RESTRICTED (terms, §1.3) |
| **RansomLook** | Victim-claim tracker, open source (AGPL), CC BY 4.0 data, keyless API | FREELY USABLE |
| **ransomwatch** | Frozen 2020–2025 claim archive (Unlicense) | FREELY USABLE (historical) |
| **AlienVault OTX** | Open threat-intel community (Pulses/IoCs); free account for API | FREELY USABLE (free account) |
| **VCDB** (vz-risk) | Open database of publicly disclosed incidents in VERIS schema; GitHub issues → validated JSON; 2026 AI-encoding skill tags provenance | FREELY USABLE |
| **VirusTotal** | File/URL/domain/IP reputation aggregator; evidence corroboration service | FREELY USABLE (non-commercial, quota-limited) / PAID |

- **Sources:** https://github.com/vz-risk/VCDB · https://filigran.io/products/opencti · https://databreaches.net/about/ · https://www.circl.lu/projects/ · https://otx.alienvault.com

### 3.2 Gaps analysis — xevents' four target capabilities

**(a) Evidence preservation (archiving proof, not just linking it):** Done well by **none**. Partially: RansomLook retains per-post screenshots/HTML (a third-party OpenCTI connector preserves them as evidence artifacts); MISP can attach files but preservation is operator-configured, not automatic. Everyone else links out (Wayback does the actual preservation, but no tool integrates archiving into its incident data model). **Core xevents differentiator: claim + archived proof stored together.**

**(b) Correction/retraction history:** Done well by **none**. Partially: MISP (field-level edit history/proposals), DataBreaches.net (informal "Update:" notes), ransomware.live (`updates` field — retraction vs edit UNVERIFIED), HIBP (`IsFabricated`/`IsRetired` flags, no public change log — UNVERIFIED), VCDB (`submitted→validated→overridden` pipeline + analyst notes — but tracks *analyst encoding*, not *source claim retraction*). No tool maintains a public, queryable retraction ledger. **False ransomware claims are a known problem; this is squarely an xevents gap to own.**

**(c) Multi-source claim reconciliation (multiple claims about the SAME incident → one record):** Done well by **none** in an automated, claim-native way. Partially: OpenCTI (graph-level entity resolution via connectors), MISP (correlation is *indicator*-based — "same IoC," not "same incident, different sources"), VCDB (analyst encodes each incident from multiple sources — closest conceptual match, but manual). Every aggregator is a *single vantage point*; the same victim on three leak sites appears as three independent rows. **A persistent, explainable incident-identity layer across sources is an xevents differentiator.**

**(d) Explainable confidence:** Done well by **none**. Fragments exist: STIX confidence scores + `created_by` (OpenCTI), taxonomies/sightings/decay (MISP), investigative prose (DataBreaches.net — strongest human-readable provenance, but unstructured), VCDB's "Encoded by AI + skill version" tagging. Nothing assembles a per-record, machine-readable "evidence → conclusion" explanation. **Fourth xevents differentiator.**

**Bottom line:** the landscape splits into platforms (MISP, OpenCTI — bring your own data, indicator-centric, no incident corpus), ransomware claim trackers (free, flat, single-vantage, no reconciliation/confidence/archiving), breach editorial/curatorial sources (human-verified but unstructured or metadata-only), community feeds (IoC/artifact layers, not incident layers), and research datasets (VCDB — normalized but analyst-driven). **All four xevents capabilities are whitespace.**

---

## 4. Entity Resolution Resources

### 4.1 OpenCorporates — PAID (free tier gone)

Largest open company database (~250M+ entities); best-in-class legal-entity matching, plus a reconciliation service. **The historical free no-auth API tier no longer exists** — all `v0.4` endpoints now require `api_token` (401 otherwise). Self-serve plans: Essentials **£2,250/yr** (500 calls/mo), Starter **£6,600/yr**, Basic **£12,000/yr**, Enterprise bespoke. Public-benefit projects (journalism, NGOs, anti-crime research) can apply for free at-scale access. API Terms require "Powered by OpenCorporates" attribution. **Skip on budget; consider the public-benefit grant.**
- **Sources:** https://opencorporates.com/pricing · https://d2ijupb52dd0cc0.cloudfront.net (API terms, Dec 2023)

### 4.2 GLEIF / LEI — FREELY USABLE

~3.36M LEI records (June 2026), 236 countries, 39 issuers. Authoritative validated legal names, addresses, and **parent/subsidiary relationships (Level 2 data)** — directly useful for "Acme Corp vs acme.com vs subsidiary." API (`https://api.gleif.org/api/v1`): no auth, no key; fuzzy legal-name search; batch lookups; 200/page pagination. Observed ~60 req/min before 429 (UNVERIFIED as official). Bulk "Golden Copy" downloadable, updated 3× daily — mirror locally for batch work. **Coverage gap: LEIs concentrate in regulated financials and large corporates; most SMEs, municipalities, hospitals, schools have none — expect low hit rates on small-business victims.** Redistribution license text UNVERIFIED — verify on gleif.org legal pages before building the public surface on it.
- **Sources:** https://www.gleif.org/lei-data/gleif-data-quality-management/quality-reports/download-data-quality-report-june-2026/2026-07-07-lei-data-quality-report-june-2026.pdf · https://github.com/api-evangelist/gleif

### 4.3 NAICS sector classification — FREELY USABLE (taxonomy); no free company→NAICS API

U.S. Census Bureau publishes the NAICS taxonomy free (2022 revision current; XLSX downloads; public domain). **No free, official per-company NAICS lookup API exists** — Census API serves aggregate statistics by NAICS code, not "what sector is this company." Practical free substitutes: Wikidata *industry* (P452), GLEIF entity categories, SEC filer SIC codes.
- **Sources:** https://github.com/zcaceres/naics-api · https://www.census.gov/data/developers/data-sets/economic-census/2022.html

### 4.4 Company-identity canonicalization APIs

- **Clearbit — dead as standalone.** Acquired by HubSpot (Dec 2023); free Logo API sunset Dec 8, 2025; enrichment now via HubSpot Breeze Intelligence, sales-led, no free tier. **Do not build on it.**
- **Diffbot — PAID:** $299/mo Startup, $899/mo Plus; Knowledge Graph ~127M orgs. Academic free program only.
- **FullContact — PAID:** no permanent free tier; enterprise quotes.
- **Wikidata — FREELY USABLE:** CC0 (public domain), SPARQL + `wbsearchentities`; company entities carry official website (P856), industry (P452), ticker (P249), parent/subsidiary (P749/P355), multilingual aliases. **Crowd-sourced, biased toward notable/large companies — small victims often missing.** Limits: 60s/query timeout, 5 parallel/IP, descriptive User-Agent required. For batch, use JSON dumps, not SPARQL. Note: WDQS graph split (May 2025); legacy full-graph endpoint removal status UNVERIFIED.
- **OpenFIGI (Bloomberg) — FREELY USABLE (scoped to securities):** free API key; 25 req/min anonymous, 250/min keyed. FIGIs are "free to use, free to issue, free to redistribute" — but identifies *instruments*, not companies; useful only for public-company victims (ticker→issuer name).
- **Sources:** https://community.hubspot.com/t5/Developer-Announcements/Upcoming-Sunset-of-Clearbit-s-Free-Logo-API/td-p/1123861 · https://www.saasworthy.com/product/diffbot/pricing · https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual

### 4.5 Open datasets for victim-name normalization — FREELY USABLE

- **SEC `company_tickers.json`** (`https://www.sec.gov/files/company_tickers.json`): ticker→CIK→legal name for ~8k exchange-traded issuers; U.S. public domain. Plus `cik-lookup-data.txt` (broader name→CIK, incl. non-ticker filers) — the standard fuzzy-name-matching seed. SEC fair access: **10 req/sec**, descriptive User-Agent required. SEC submissions also carry **SIC industry codes** — a free company→sector signal for filers.
- **Fortune 500 lists:** exist as GitHub-mirrored CSVs; canonical machine-readable endpoint and license terms UNVERIFIED — candidate, not relied-upon.

### 4.6 Recommended free-tier entity-resolution pipeline for xevents

A no-cost, re-publishable stack where each enrichment step is itself an *observation* (source + timestamp + confidence):

1. **Local normalization layer (own code):** lowercase/strip, legal-suffix removal (LLC, Inc., GmbH, Ltd., S.A.S.), abbreviation expansion, TLD/URL extraction from leak posts, alias table seeded from correction history.
2. **SEC tickers + CIK lookup (free, public domain):** exact/fuzzy match first — instantly resolves public-company victims to CIK + legal name + SIC sector at zero API cost.
3. **GLEIF API / Golden Copy (free, no key):** fuzzy legal-name search for private companies; parent/subsidiary data resolves the subsidiary-vs-parent ambiguity; entity status flags (ISSUED/LAPSED/MERGED) feed the confidence model. Mirror the Golden Copy locally to avoid the ~60/min ceiling.
4. **Wikidata (free, CC0):** secondary name/alias match; official-website (P856) cross-check against domains in breach notices; industry (P452) as sector signal. Dumps for bulk, SPARQL for ad-hoc.
5. **Census NAICS 2022 tables (free, public domain):** embed the taxonomy locally as the sector spine; SIC→NAICS concordances and Wikidata-industry→NAICS as low-confidence heuristic mappings, recorded as observations.
6. **OpenFIGI (free key):** ticker/ISIN→FIGI→issuer-name as corroborating observation for public-company victims.

**Residual gap to own:** none of the free sources reliably identify SMEs (no LEI, no Wikidata entry, no SEC filing) — the local alias table plus a human-review queue is the honest, documented coverage boundary.

---

## 5. Analytics Prior Art

### 5.1 Compromise-to-disclosure lag

- **Silobreaker (2024, 2023 data):** 922 ransomware attacks analyzed. Public reporting **~41 days on average after initial attack** (46 days for 2022); <5% reported within one day; **~50% of affected orgs never publicly admitted the attack** (up from ~25%); **~90-day average delay** before customers are informed of breached data. Underlying dataset proprietary (PAID/RESTRICTED). UNVERIFIED whether a newer edition exists. — https://securitybrief.com.au/story/report-reveals-lag-in-disclosure-of-ransomware-attacks-in-2023
- **Bitsight (~2022):** discovery + disclosure "a long, slow process — to the tune of **105 days**" (pre-SEC-rule baseline); report free with registration, data restricted. — https://www.bitsight.com/resources/can-new-regulations-accelerate-cyber-incident-disclosure-process
- **Mandiant M-Trends (dwell time, adjacent metric):** 2024 global median dwell **11 days** (first increase in years; 205 days in 2014); ransomware-related intrusions 21% of 2024 intrusions. Report free, data restricted. — via https://www.securityscientist.net/content/files/2026/06/ransomware-dwell-time.pdf (UNVERIFIED against primary M-Trends PDF)
- **Secureworks CTU:** ransomware dwell 4 days (IR) / 3 days (MDR); 83% of 2024 ransomware binaries deployed outside business hours. — https://www.helpnetsecurity.com/2025/04/03/breach-median-time/
- **Takeaway:** No open, incident-level dataset links per-incident compromise date → disclosure date. All lag figures are vendor aggregates over private caseloads.

### 5.2 Ransomware victim trends by sector

- **Coveware by Veeam (quarterly; confirmed through Q3 2025):** % paying ransom (Q3 2025: **23%** — record low), avg/median ransom (Q2 2025: avg **$1.13M** +104% QoQ, median **$400K**), victim industry mix (professional services, healthcare, consumer services), median victim size (Q3 2025: 362 employees), initial-access vectors, group shares. Reports free; underlying IR/negotiation caseload restricted. UNVERIFIED: series continuation into Q4 2025/2026. — https://www.coveware.com/blog/2025/4/29/the-organizational-structure-of-ransomware-threat-actor-groups-is-evolving-before-our-eyes
- **Chainalysis Crypto Crime Report (annual; 2026 ed. covers 2025):** **$820M+ on-chain ransom payments in 2025** (−8% YoY); **~8,000 leak events in 2025** (+50% YoY, most active year on record, using **eCrime.ch** data); ~28% of ransoms paid (possible all-time low). Report free; data restricted. — https://www.chainalysis.com/blog/crypto-ransomware-2026/
- **Verizon DBIR 2026 (2025 data year):** **ransomware in 48% of confirmed breaches**; 69% of victims didn't pay; median ransom paid $139,875; 96% of victims SMBs; third-party involvement in 48% of breaches; vulnerability exploitation top initial-access vector (31%); 31,000+ incidents / 22,000+ breaches / 145 countries. Report free (PDF); data restricted (aggregate-only). Sector snapshots for healthcare and public sector. — https://www.verizon.com/business/resources/T70/reports/2026-dbir-data-breach-investigations-report.pdf

### 5.3 Exploited-vulnerability tracking

- **CISA KEV — FREELY USABLE:** ~1,400+ CVEs with confirmed in-the-wild exploitation. Machine-readable JSON (`https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`) and CSV, no auth, updated in batches several times/week (active through Sep 2026). Each entry carries a **"Known To Be Used in Ransomware Campaigns?"** flag — **but with no linkage to specific incidents or campaigns. That is exactly the gap xevents can fill.**
- **VulnCheck KEV — FREELY USABLE (free account):** 3,600–3,700+ exploited CVEs (~175% more than CISA), claims ~27 days earlier than CISA on average, with exploitation-evidence citations and PoC links; 2026 report: 884 KEVs with first-time 2025 exploitation evidence, 28.96% exploited on/before CVE publication day. Still CVE-level only — **no per-incident CVE→victim mapping anywhere found.**
- **Sources:** https://pagecrawl.io/blog/cisa-kev-catalog-cve-monitoring-security-teams · https://www.businesswire.com/news/home/20250507328009/en/VulnCheck-KEV-Surges-to-Track-More-than-3600-Known-Exploited-Vulnerabilities

### 5.4 Sector/vertical breach statistics

- **ITRC Annual Data Breach Report (2025 ed., Jan 2026) — reports FREELY USABLE, data restricted:** **3,322 U.S. data compromises in 2025** (record high; +5% vs 2024); 278.8M victim notices; by industry: financial services 739 (22%), healthcare 534 (16%), professional services 478 (14%), manufacturing 299 (9%), education 188 (5.6%); **70% of notices included no attack/cause information** (worsening transparency trend). Incident-level dataset internal. — https://www.infosecurity-magazine.com/news/us-data-breaches-record-high/
- **HHS OCR portal — FREELY USABLE data, scrape-only:** incident-level healthcare breach records ≥500 individuals since 2009 (see §2.3).

### 5.5 Gap analysis: well-served vs genuinely missing

**Already well-served by public analysis (reference, don't duplicate):** aggregate ransomware economics (Coveware, Chainalysis, DBIR — free reports, quarterly/annual); breach counts by industry (ITRC, DBIR, HHS OCR); CVE-level exploitation tracking (CISA KEV, VulnCheck KEV — free, machine-readable, multi-weekly); aggregate lag statistics (Mandiant, Secureworks, Silobreaker, Bitsight).

**Genuinely missing — xevents' open lane:**
1. **Per-incident compromise→disclosure timelines.** Every lag figure is an aggregate over a private caseload. No open dataset records initial compromise, victim notification, leak-site listing, and public acknowledgment side by side per incident.
2. **CVE→incident linkage.** KEV flags "known ransomware use" at CVE level but maps no CVE to any specific victim or campaign.
3. **Reconciled, correction-carrying incident records.** All public sources treat single-source claims as final; none preserve correction history or reconcile conflicting claims.
4. **Open incident-level ransomware victim dataset.** eCrime.ch and vendor scrapes hold raw leak-site data but don't publish it openly in bulk; everyone else publishes aggregates.

---

## 6. Feasibility and Blockers

*(Reported considerations from sources, not legal advice.)*

### 6.1 Collection practicalities — PROCEED WITH CARE

- **Leak sites are Tor hidden services.** Direct scraping is technically demanding: substantial compute (concurrent runners, queue management, storage); .onion discovery via pastes/IRC/Telegram (well-known indexes rarely suffice); volatility and connection unreliability are core analyst challenges; ~82% of analyzed dark-web content is mirrored (https://securityaffairs.com/88562/deep-web/scraping-tor-network.html, https://arxiv.org/pdf/2504.16836.pdf). **In practice most researchers rely on aggregators** (Emsisoft's 2023–2025 census used RansomLook.io + Ransomware.live). Checking leak sites directly "carries both security and legal exposure risks depending on your jurisdiction" (https://malware.news/t/top-10-active-ransomware-groups-to-watch-in-2026/125522).
- **Volatility, rebrands, takedowns (2024–2026):** Operation Cronos (Feb 2024) disrupted LockBit (34 DLS servers seized); ALPHV/BlackCat FBI-seized Dec 2023, relaunched, then exit-scammed Mar 2024; RansomHub went offline Mar 2025; 8Base takedown 2025; Hunters International → World Leaks (Jul 2025). Rebrand chains (DarkSide→BlackMatter→ALPHV; Royal→BlackSuit) complicate group identity. **The ecosystem is fragmenting:** 85+ active groups, 1,592 new victims in Q3 2025 alone, 45 new groups began publishing in 2025, top-10 share fell 71%→56%; Emsisoft counts ~70 groups (2023) → 126–141 (2025), ~8,000 claimed victims in 2025. Takedowns don't reduce aggregate volume — "operators scatter and regroup within days."
- **Evidence archiving:** Screenshots are the demonstrated standard (every ransomware.live entry carries an archived "Leak Screenshot"). WARC is the established web-archive format, but **no public source confirms major DLS trackers use WARC** (UNVERIFIED). Recommended posture: timestamped captures (screenshot + raw HTML/metadata) per observation; WARC as enhancement. ransomware.live flags "Duplicate Entry" on victim pages — dedup handling exists in the wild.
- **Implication:** Aggregator APIs are the practical bootstrap, but create licensing dependency (§6.2). Own Tor crawlers demand onion-discovery and anti-volatility engineering. Either way, **rebrand/successor-group tracking and high-frequency polling are mandatory** — precisely where xevents' correction-history model adds value.

### 6.2 Licensing / ToS — PROCEED WITH CARE (most consequential constraint)

- **ransomware.live T&C (fetched 2026-09-17)** expressly bars raw-data republication and API-style redistribution, and unapproved commercial use — **xevents cannot be built on its dataset without written permission.**
- **Facts are not copyrightable** (victim names, dates as facts are freely reusable), but the **EU sui generis database right** lets makers of databases with "substantial investment" block extraction/re-utilization of the whole or a substantial part for 15 years — ransomware.live is French-law governed, squarely in this regime.
- **Practical read:** building from **primary sources (direct DLS collection)** sidesteps aggregator database rights; **bulk-deriving from ransomware.live's aggregated database** (especially via its API, whose T&C already forbids it) is the risk zone. Verifying individual facts against the aggregator ≠ extracting its database wholesale, but the line is gray.
- **Scraping (U.S.):** *hiQ Labs v. LinkedIn* (9th Cir. 2022) held scraping publicly available website data likely doesn't violate the CFAA, but "the law remains unclear in many respects" — reported consideration, not clearance.
- **Cleanest ingestion posture:** RansomLook (**CC BY 4.0** — attribution only) + ransomfeed.it (free incl. commercial use) + **independent primary collection** for anything beyond them. Get written permission before touching ransomware.live data at scale; treat ecrime.ch as a paid enrichment option.

### 6.3 Legal/ethical — public research surface naming victims — PROCEED WITH CARE

- **Defamation risk is real.** Documented misidentifications: Clop listed "Thames Water" when the victim was South Staffs Water (later corrected). Industry practice is **claim-framing + correction channels, not verification**: GalaxyWarden (2026) labels every page "a public listing … the attacker's claim … we have not independently verified"; ransomware.live's T&C disclaims confirmation; Undercode News (Sep 2026): "a public ransomware listing … does not by itself establish … whether the organization was actually compromised." **This is exactly xevents' evidence-first design — the risk is managed by the design, not eliminated by it.**
- **No known lawsuits against ransomware trackers or breach aggregators found** (UNVERIFIED — absence of search results, not proof). Adjacent litigation targets breached companies, not trackers (e.g., *Onix Group* class action; *Clemens v. ExecuPharm*).
- **GDPR posture:** Breach-notification duties sit with controllers, not trackers. For a tracker handling data that may include personal data (named individuals, emails in ransom notes): document a lawful basis / public-interest research justification, pseudonymize, minimize. **Observed model to copy:** ransomware.live and GalaxyWarden index only publicly visible listing metadata and screenshots — **no acquisition, hosting, or redistribution of stolen content or personal data.**
- **Correction-request handling (existing practice):** ransomware.live §9 formal removal/dispute process (discretionary, case-by-case); GalaxyWarden published takedown policy with prompt correction of material shown inaccurate. **xevents must ship a published dispute/correction channel from day one.**
- **Operator safety:** Passive collection only; no interaction with criminal infrastructure (cf. the "Ransom Busters" case — unauthorized access to threat-actor infrastructure assessed as likely CFAA-violating). No verified retaliation cases against tracker operators found (UNVERIFIED), but the environment warrants hygiene: low profile, isolated infra, no engagement.

**Overall:** No BLOCKER classifications. All three sub-areas rate PROCEED WITH CARE. The single most consequential constraint is **§6.2**: xevents cannot be built on ransomware.live's raw data without written permission; the licensing-safe architecture is independent collection from primary sources (or the CC-BY RansomLook feed), which in turn demands the Tor-crawling and rebrand-tracking investment flagged in §6.1.

---

## 7. Top Blockers / Hardest Problems (synthesis)

Ranked by consequence for the project:

1. **Licensing-safe ingestion is the binding constraint.** The richest free feed (ransomware.live) forbids republication; the cleanest open feed (RansomLook, CC BY 4.0) has the sparsest metadata (no country/sector). The licensing-safe architecture is independent primary DLS collection — which means real Tor-crawler operations (onion discovery, volatility handling, rebrand tracking). This is the project's biggest engineering investment and its biggest legal protection, in one.
2. **Entity resolution for SMEs.** Free sources (SEC tickers ~8k public issuers; GLEIF ~3.36M mostly large/regulated entities; Wikidata biased to notable companies) systematically miss small-business victims. OpenCorporates' free API tier is dead (from £2,250/yr); Diffbot/FullContact are paid; Clearbit is gone. Plan: local normalization + alias table + human-review queue, and document the coverage boundary honestly.
3. **De-listing / removal events are invisible.** Groups remove victims who pay; no aggregator publishes a "listing removed" history. xevents must detect removals itself via re-polling and diffing — and removals are among the most valuable observations (evidence of payment, false claim, or takedown).
4. **Evidence preservation has no off-the-shelf solution.** No surveyed tool archives claim-level proof as a first-class record. Build: timestamped screenshot + raw HTML/metadata capture per observation (WARC optional), content-addressed storage, retention policy. Leak sites die; without capture-at-ingest, evidence rots.
5. **False claims and hoax injection are live threats.** Documented misnamings (Clop/Thames Water) and the June 2026 Maine AG hoax filings (fake VRChat/Discord breach reports that took a state register offline) prove public registers get poisoned. The correction/retraction ledger isn't a nice-to-have — it's load-bearing for credibility, alongside claim-framing language and a published dispute channel.

## 8. Recommended Ingestion Architecture (synthesis)

A workable, licensing-clean, no-budget starting stack:

| Layer | Source | Classification |
|---|---|---|
| Ransomware claims (primary) | **RansomLook API** (CC BY 4.0, attribution) — no-key, active | FREELY USABLE |
| Ransomware claims (gap-fill) | **ransomfeed.it** RSS/API (free incl. commercial, 60-min cadence, analyst-added country) | FREELY USABLE |
| Ransomware claims (independent) | **Own Tor crawler** (deepdarkCTI directory as seed list; CIRCL AIL Framework AGPL as reference) | own build |
| Ransomware metadata (reference only) | ransomware.live v2 — query for enrichment cross-checks, **do not republish** (personal-use terms) | RESTRICTED |
| Historical baseline | ransomwatch frozen 2020–2025 archive (Unlicense) | FREELY USABLE |
| Breach disclosures (public companies) | **SEC EDGAR** — efts full-text search + submissions JSON + bulk ZIP (10 req/s, descriptive UA) | FREELY USABLE |
| Breach disclosures (states) | **CA AG CSV** + **WA AG Socrata API**; others ad-hoc | FREELY USABLE |
| Breach disclosures (healthcare) | **HHS OCR portal** — community scraper pattern (~70 reqs full archive) | FREELY USABLE (scrape) |
| Breach catalog (enrichment) | **HIBP keyless breach catalog** (CC BY 4.0) | FREELY USABLE |
| Exploited vulns | **CISA KEV** JSON/CSV (no auth); VulnCheck KEV (free account) | FREELY USABLE |
| Entity resolution | SEC tickers → GLEIF → Wikidata → Census NAICS → OpenFIGI | FREELY USABLE |
| Incident schema reference | **VCDB / VERIS** schema (open) | FREELY USABLE |
| Platform reference | **MISP / OpenCTI** data models (AGPL / Apache 2.0) — model on, don't rebuild | FREELY USABLE |

**What to verify before writing the docs:** ransomware.live PRO T&C republication terms (if PRO enrichment is wanted); GLEIF redistribution license text; HHS OCR bulk-export existence; Coveware series continuation; whether any commercial CTI vendor offers a usable free tier (none found).

---

*End of report. Research conducted September 17, 2026 via text search and page fetch. UNVERIFIED flags mark claims needing confirmation before they become design inputs.*
