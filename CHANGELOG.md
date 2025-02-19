# Changelog

## [1.1.0](https://github.com/dhis2/dhis2-server-tools/compare/v1.0.0...v1.1.0) (2025-02-19)


### Features

* Add support for selecting minor versions ([#43](https://github.com/dhis2/dhis2-server-tools/issues/43)) ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Begin support for Java version selection in DHIS2 2.42 ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Start separating playbooks (SSL config, instance creation, etc.) ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Validate `dhis2_version` input ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))


### Bug Fixes

* Correct timezone settings for host and LXD containers ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Ignore `*.template` and `__pycache__/` files ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))

## [1.0.0](https://github.com/dhis2/dhis2-server-tools/compare/v1.0.0...v1.0.0) (2025-02-19)


### Features

* Add support for selecting minor versions ([#43](https://github.com/dhis2/dhis2-server-tools/issues/43)) ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Begin support for Java version selection in DHIS2 2.42 ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Start separating playbooks (SSL config, instance creation, etc.) ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Validate `dhis2_version` input ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))


### Bug Fixes

* Correct timezone settings for host and LXD containers ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))
* Ignore `*.template` and `__pycache__/` files ([38faeab](https://github.com/dhis2/dhis2-server-tools/commit/38faeab50ebaa993208cad264b627bd75af6730a))

## 1.0.0 (2025-02-13)


### Features

* Add suppor for dynamically setting java_version, tomcat_version ([8ed453e](https://github.com/dhis2/dhis2-server-tools/commit/8ed453e05bced638fea84be1a5e472b89a965810))
* add support for custom munin_base_path configuration ([6175ede](https://github.com/dhis2/dhis2-server-tools/commit/6175ede7a0967225e88ca1c62f5396faa6863423))
* Added munin_base path on apache3 proxy, custom dynamic inventory ([d0c158e](https://github.com/dhis2/dhis2-server-tools/commit/d0c158eab83f2a47b996313c544631569d40d546))
* Added support for multiple domains ([59df778](https://github.com/dhis2/dhis2-server-tools/commit/59df778eb51acff11cbdd608182e5520332f01ca))
* Added support for nginx, apache2 tomcat9  munin monitoring. ([1672d8e](https://github.com/dhis2/dhis2-server-tools/commit/1672d8eecb512abb6f7ad7f9bcff79a2321d2f58))
* adding host_vars templates | securing_munin ([7658eeb](https://github.com/dhis2/dhis2-server-tools/commit/7658eeb4e08b19b1d83230f7b858529c3a94f7c5))
* backups, variables refactor, securing glowroot and munin ([55378a8](https://github.com/dhis2/dhis2-server-tools/commit/55378a8fb856e87bfff2b1de035275c84adf2573))
* Enable upgrades manually ([ec96441](https://github.com/dhis2/dhis2-server-tools/commit/ec964415d26823abdf88fb2dd2f000e70ba19066))
* Introducing Tags ([0ec7ca6](https://github.com/dhis2/dhis2-server-tools/commit/0ec7ca66f8c8f8edd023f6efdbfa65d7e69d94a7))
* Minor refactoring, fix glowroot logins ([986847e](https://github.com/dhis2/dhis2-server-tools/commit/986847ea9242a4845b8d9942931d99c02bdce579))


### Bug Fixes

* made glowroot tasks idempontent ([8ed453e](https://github.com/dhis2/dhis2-server-tools/commit/8ed453e05bced638fea84be1a5e472b89a965810))
* **release:** add --is-collection yes to antsibull-changelog ([aed9a41](https://github.com/dhis2/dhis2-server-tools/commit/aed9a4130594b4894881ba880110f5e4655d4626))
* **release:** remove duplicate --is-collection ([#39](https://github.com/dhis2/dhis2-server-tools/issues/39)) ([cb95f86](https://github.com/dhis2/dhis2-server-tools/commit/cb95f86db6446a08efb8e9ceaa58b9c3e496bfcb))
* Support dhis2 version  2.40 ([b90659f](https://github.com/dhis2/dhis2-server-tools/commit/b90659fcf1dfefaf24983cd5c1e493d5b5274594))
* tighten up glowroot permissions ([3134f83](https://github.com/dhis2/dhis2-server-tools/commit/3134f835e3a4446b3bc2b96bcff4f30c5aeac7e7))
