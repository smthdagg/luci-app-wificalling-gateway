# Security Policy

## Supported versions

Security fixes are provided for the latest release line.

## Reporting

Do not publish credentials, complete node URIs, router backups, UCI exports, or generated `/var/run/wificalling-gateway/sing-box.json` in an issue. Open a GitHub security advisory for vulnerabilities and include only sanitized reproduction data.

## Local secrets

Node credentials are stored in `/etc/config/wificalling-gateway`; generated runtime data is under `/var/run/wificalling-gateway`. The service enforces mode `0600`, but administrators remain responsible for router access, backups, logs, and exported support bundles. Rotate any credential exposed publicly.

## Trust boundary

The package runs as root because it manages policy routing and nftables. Install packages only from this repository's releases or build from reviewed source. Verify the published SHA-256 checksum before installation.
