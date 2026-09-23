# xevents

**Research public incident claims without republishing the people and organizations behind them.**

xevents turns observed ransomware listing claims into name-free, weekly sector
aggregates for security practitioners and researchers. It preserves the evidence
privately and keeps uncertainty visible in the public results. A listing is a
claim, not confirmation that a breach occurred.

[Open the research app](https://neilweitzel.github.io/xevents/) ·
[Read the methodology](docs/research-guide.md) ·
[Explore the documentation](docs/README.md)

## What you can use it for

- **Explore observed activity:** compare published claim counts by sector and
  retrieval week, without a public directory of named victims or threat actors.
- **Build a research snapshot:** filter the view and download the selected
  aggregate data as JSON.
- **Understand the limits:** see withheld cells, data freshness and the coverage
  boundaries alongside the numbers.

This is not a breach registry, an organization risk score, a complete census of
ransomware activity or a feed for automated blocking. Unlike
[xfeeds](https://github.com/neilweitzel/xfeeds), xevents is built for interpreting
incident claims over time, not distributing indicators for enforcement.

## Current status

The [public app](https://neilweitzel.github.io/xevents/) is available. The
unattended release integration is being prepared for activation and research
release-candidate burn-in; it is not yet a graduated production service.
Private scheduled collection is already operating.

The app loads published research data by default. If no dataset has been
published, it says so instead of substituting sample numbers. An explicitly
labeled [synthetic demo](https://neilweitzel.github.io/xevents/?demo=1) is available
separately and must not be cited as research.

## How to read the results

- **Claims, not confirmed incidents:** the initial source is RansomLook.
  Repeated observations do not provide independent corroboration.
- **Retrieval time, not attack time:** reporting weeks start on Monday in UTC,
  based on when xevents first retrieved a claim.
- **Partial coverage:** the initial collector samples a bounded recent-record
  window. It cannot establish how many claims were missed or whether a listing
  was later removed.
- **Conservative classification:** the RC uses description-based sector
  heuristics. Ambiguous descriptions remain unclassified rather than acquiring
  an invented sector or confidence score.
- **Small cells stay withheld:** counts below five, including zero, are shown as
  withheld. Missing and withheld values are not evidence of no activity.

The [research guide](docs/research-guide.md) explains appropriate comparisons,
exports, privacy limitations and the difference between a claim and an incident.

## How it works

```text
Public listing metadata
        |
Private collection and evidence preservation
        |
Automatic eligibility, sector aggregation and exact-output privacy checks
        |
Signed release, protected merge and verified deployment
        |
Public research app and aggregate exports
```

The full automated release path is the RC activation target. Routine eligible
records do not require individual human approval. Privacy exceptions remain
withheld; failed integrity or publication checks stop that release and preserve
the previous site. The browser reads public aggregates only and has no access
to private evidence or credentials.

Raw source text, organization and threat-actor names, screenshots and
record-level evidence stay private. The public repository contains the app,
aggregate export surface, verification code and the methodology needed to
examine the design. Public export hashes verify published bytes; they are not
record-level disclosures of private evidence.

## Go deeper

- **Research and reuse:** [research guide](docs/research-guide.md),
  [source specification](docs/source-spec-ransomlook.md) and
  [glossary](docs/glossary.md).
- **Privacy and corrections:** [naming policy](docs/naming-policy.md),
  [correction process](docs/dispute-process.md) and
  [RC research/privacy memo](docs/research-privacy-memo.md).
- **Engineering:** [app development](app/README.md),
  [automated RC contract](docs/adr/0022-unattended-research-rc.md) and
  [architecture decisions](docs/adr/).
- **Contributing:** start with [AGENTS.md](AGENTS.md) and the
  [documentation map](docs/README.md). Never put private evidence, credentials or
  affected-party identities in public issues or pull requests.

## Attribution

The initial derived source is [RansomLook](https://www.ransomlook.io/).
RansomLook identifies its website, API and datasets as
[CC BY 4.0](https://www.ransomlook.io/about). xevents transforms observations into
restricted aggregate outputs; its classifications and limitations are its own.
Source licensing does not make sensitive personal information safe to publish.
