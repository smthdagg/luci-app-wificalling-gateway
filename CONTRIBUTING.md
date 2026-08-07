# Contributing

Issues and pull requests are welcome in Chinese or English. Never include live node credentials, public/private keys, complete subscription URLs, router backups, or personal IP information.

For code changes:

1. Add or update a regression test first.
2. Run `python3 -m unittest discover -s tests -v`.
3. Run shell and JavaScript syntax checks described in `docs/en/BUILD.md`.
4. Test installation and rollback on a disposable OpenWrt/ImmortalWrt device or VM.
5. Explain firewall, routing, compatibility, and secret-handling impact in the pull request.

Commits should use a clear conventional prefix such as `feat:`, `fix:`, `docs:`, or `test:`.
