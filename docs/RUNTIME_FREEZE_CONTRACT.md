# Hosted runtime freeze and controlled recovery

Status: bounded locked cold-start/controlled recovery PASS in run 35166865310.
Phase 0 remains RUNNING, full G0 NOT_EVALUATED.

Target ubuntu-24.04 x64 and exact Python 3.12.14 via .python-version. Two independent
cold jobs use no saved pip/browser/model cache. requirements-tools.lock pins pip,
setuptools, wheel and packaging; requirements-probe.lock pins all observed runtime
dependencies with PyPI SHA256 release-file allowlists. All downloads require hashes;
runtime resolution is disabled, build isolation is disabled and pip check must pass.
ANTLR 4.9.3 has only a source release; its verified sdist builds with locked tools.
This does not claim bit-identical locally built wheel timestamps.

requirements-probe.txt remains the root-dependency declaration; bootstrap exclusively
uses reviewed locks. No runtime command refreshes the locks or expected hashes.
Updates require new inventory/review and hosted cold/source regression. Public PyPI
is explicit; no credentials or private package index is required.

runtime-manifest.json pins 29 combined runtime/build packages, six RapidOCR resources
(three ONNX files plus package YAML configurations), original resource SHA256s and
canonical Playwright browser-registry JSON hash. Wheel/sdist hashes protect package
bytes; registry hash protects browser revision/content, not JSON formatting.
Missing ONNX resources download only from the unique versioned HTTPS URL captured
in inventory. Verify SHA256 before promoting downloaded bytes or instantiating OCR.
Existing wrong bytes are not silently replaced. Missing non-model configuration,
unexpected ONNX files, traversal/duplicate manifest entries, Python/OS/architecture,
package or lock/hash drift fail before source collection. Rejected download bytes
and failure metadata are retained.

GitHub stable Actions verified 2026-09-17, all declaring Node 24:
- checkout v7.0.1: 3d3c42e5aac5ba805825da76410c181273ba90b1
- setup-python v7.0.0: 5fda3b95a4ea91299a34e894583c3862153e4b97
- upload-artifact v7.0.1: 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a

All workflows use immutable action SHAs; credentials are not persisted and artifact
ZIP behavior remains the default. No Node downgrade flags or saved desktop profile.
The Ubuntu runner image/system apt libraries remain GitHub-maintained inputs; record
image version/platform. This is a locked application runtime, not an immutable OS.

Bootstrap records stages and exit codes before/after package, integrity and browser
installation. Its error trap leaves FAIL; artifact upload uses always(). No error is
interpreted as missing certification or a valid product/document result.

Controlled recovery copies the actual verified model/configuration resources into
an isolated runtime directory. Append known bytes to one copied ONNX; preserve its
raw corrupted bytes and FAIL hashes, require the gate to reject it, restore from
the original verified model and retain separate recovered observations. Original
installed resources are untouched. This proves integrity blocking and recovery from
trusted bytes, not arbitrary network/WAF recovery or a source retry guarantee.

Acceptance: two distinct cold jobs, PDF/CPU-OCR/Chromium/live probes, all tests,
controlled corrupted-copy rejection/recovery and full 12-source plus 9-EPA regression
using new pins/Python. Intermediate artifacts include bootstrap.json, dependencies,
integrity reports, corrupted copy bytes, probe.json and source response evidence.
Raw artifacts have 14-day retention; compact manifests are not replay binaries.

Inventory run 35166528591 / code d26c8a094fb98a6cea2338c312c9dbcc2a3e7c5d,
artifact 10474938764 (ZIP SHA256
04088bbb00c7957343f6ac7804229529e615aa6794e012d93ec79191fd6cd59c).
Initial workflow omitted diagnostic-directory preparation and failed before
inventory; retained in runtime-freeze-failure-history.json. No package/model/source
absence conclusion was made. The original job log confirms that missing directory;
its hash/error are retained in the failure history.

Final code bf6078724ebda11384860219be82f63bfc82b4de:
- Two independent cold jobs in run 35166865310 passed 180 tests, six resource hash
  checks, expected corrupted-copy rejection, verified-copy recovery and four live
  probe checks (disk, embedded/image-only PDF OCR, Chromium/Samsung, EPA catalog).
- Full source regression 35166865304 passed all 12 source legs with 180 tests.
- EPA regression 35166865352 passed nine jobs with the 12 query-boundary tests.
- Separate hosted runner probe 35166865316 passed tests and all live probes.

Image ubuntu24 / 20260907.300.1 and actual browser 153.0.8010.12 were observed.
Complete compact proof is docs/evidence/runtime-freeze-recon.json: action/lock/model
configuration, committed Linux lockfile hashes, job/runner names, before/after FAIL
and recovery hashes, artifact ZIP hashes/expiry and live-probe results. Windows
working-copy CRLF is not a new expected Linux checksum. Corrupted binary bytes are
retained in raw artifacts; reports never overwrite the failed observation.
Runtime PASS does not close G0 or approve audit semantics. Next: consolidated G0
evidence/gap review. No LLM or provider credentials in Actions runtime.

Primary manifests:
- [checkout](https://raw.githubusercontent.com/actions/checkout/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml)
- [setup-python](https://raw.githubusercontent.com/actions/setup-python/5fda3b95a4ea91299a34e894583c3862153e4b97/action.yml)
- [upload-artifact](https://raw.githubusercontent.com/actions/upload-artifact/043fb46d1a93c77aae656e7c1c64a875d1fc6a0a/action.yml)
