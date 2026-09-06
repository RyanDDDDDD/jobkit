# jobkit — Claude Code plugin marketplace

A single-plugin marketplace. The plugin lives in
[`plugins/job-application/`](plugins/job-application/) — see its
[README](plugins/job-application/README.md)
([中文](plugins/job-application/README.zh-CN.md)).

## Install

```
claude plugin marketplace add RyanDDDDDD/jobkit
claude plugin install job-application@job-application-marketplace
```

Then run Claude Code from a **separate private working folder** (not this repo) and use
`/setup` → `/apply` → `/interview`. Full setup in the plugin README.
