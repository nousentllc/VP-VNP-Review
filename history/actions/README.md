# Preserved hosted verification

The release tree contains the [unaltered Actions artifact ZIP](../../checks/pass14_linux_artifact.zip) from run `45691617731` and the [full decoded job log](pass14-job-139478246305.log.gz) for job `139478246305`. The ZIP contains the outer Lake build log, effective Comparator configuration and inner Comparator log. The job log is the UTF-8 response returned by GitHub's job-log endpoint, including its byte-order mark, compressed with gzip for this archive. All 14 previously recorded timestamped excerpts match at their original line numbers.

| Record | SHA-256 |
|---|---|
| Original Actions artifact ZIP | `51c556d89448e6574e57dc4cceca799fd187d786fb7807516d65bc5629772307` |
| Preserved job log, gzip | `527f05bd0aec22d39e640afb34a3b27604f2e40193d571a4c39425271777682f` |
| Job log, decompressed | `f4202727be9e16f795a32cf2e4df28be0917001edfb9102c821ba4ed81b57e21` |

The review team launched the hosted run. It exercised a separate Linux environment and both kernels. Third-party reproduction of the release candidate remains pending. [Hosted job](https://github.com/nousentllc/VP-VNP-Review/actions/runs/45691617731/job/139478246305) · [Machine receipt](../../checks/pass14_comparator.json) · [Timestamped excerpts](../../reconciliation/edition12-hosted-log-excerpts.json).
