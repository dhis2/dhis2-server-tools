# Changelog

## [1.4.0](https://github.com/dhis2/dhis2-server-tools/compare/v1.3.0...v1.4.0) (2026-02-10)


### 🎉 New Features

* support for nginx proxy protocol ([2d2c6da](https://github.com/dhis2/dhis2-server-tools/commit/2d2c6da1b543afb49d34a91d8f52fef1d2f524bb))
* upgrade nginx ([2d2c6da](https://github.com/dhis2/dhis2-server-tools/commit/2d2c6da1b543afb49d34a91d8f52fef1d2f524bb))


### 🐛 Bug Fixes

* dhis2-deploy-war detect tomcat version automatically ([2d2c6da](https://github.com/dhis2/dhis2-server-tools/commit/2d2c6da1b543afb49d34a91d8f52fef1d2f524bb))

## [1.3.0](https://github.com/dhis2/dhis2-server-tools/compare/v1.2.0...v1.3.0) (2026-01-28)


### 🎉 New Features

* add backups role, Apache Doris support, and deploy.sh improvements ([0cfa14b](https://github.com/dhis2/dhis2-server-tools/commit/0cfa14bbb036e45c37f31c91ed16308a5f8f5862))


### 🐛 Bug Fixes

* optimized deploy.sh ([#69](https://github.com/dhis2/dhis2-server-tools/issues/69)) ([abfd676](https://github.com/dhis2/dhis2-server-tools/commit/abfd6760d2421e56343494b8ceb8089f4e84ab04))
* proxy configuration for apache2 and nginx ([0cfa14b](https://github.com/dhis2/dhis2-server-tools/commit/0cfa14bbb036e45c37f31c91ed16308a5f8f5862))

## [1.2.0](https://github.com/dhis2/dhis2-server-tools/compare/v1.1.0...v1.2.0) (2026-01-19)


### 🎉 New Features

* add linting, security scanning, and testing ([d8968f7](https://github.com/dhis2/dhis2-server-tools/commit/d8968f7635fb3931ac155404cb64349c54cb4cf4))
* Added distributed install from a laptop, ([225b6b2](https://github.com/dhis2/dhis2-server-tools/commit/225b6b25c046bcacbabe62a9cc04417017767afe))
* Adding posgresql.json grafana dashboards ([5770707](https://github.com/dhis2/dhis2-server-tools/commit/5770707cc29f6620c9f825004edca9c4225ef90e))
* Allowed grafana access with ip address ([f3b0049](https://github.com/dhis2/dhis2-server-tools/commit/f3b0049396a41f246c466d34d172dd5427c9ea34))
* ansible install script ([6a18b1f](https://github.com/dhis2/dhis2-server-tools/commit/6a18b1f5a7fcf4cefed86a6aae30a595e9faba05))
* apache doris deploy playbook ([b13ddf1](https://github.com/dhis2/dhis2-server-tools/commit/b13ddf1bcebb1571234677ff728046a81f9ec645))
* Apache Doris deploy playbook ([b13ddf1](https://github.com/dhis2/dhis2-server-tools/commit/b13ddf1bcebb1571234677ff728046a81f9ec645))
* continured developentmt on delete instance playbook ([0b66c79](https://github.com/dhis2/dhis2-server-tools/commit/0b66c7964ff021823504a599a63d40ff58cbbfe2))
* Custom port for http and https ([15a310e](https://github.com/dhis2/dhis2-server-tools/commit/15a310ef4c595e2dcb396ce0aacf5781d7edcd96))
* Delete instance playbook | Added support for deleting hosts ([845dc86](https://github.com/dhis2/dhis2-server-tools/commit/845dc86b0e2e813e659a4696c2de9d76c66df745))
* Delete instance playbook working for apache2 proxy ([2f623ab](https://github.com/dhis2/dhis2-server-tools/commit/2f623aba5e3c849fd6a40ebe7be9ba204aa397ba))
* Delete instance working on nginx, site.j2 ([2f623ab](https://github.com/dhis2/dhis2-server-tools/commit/2f623aba5e3c849fd6a40ebe7be9ba204aa397ba))
* dhis2 config for apache doris ([ab29186](https://github.com/dhis2/dhis2-server-tools/commit/ab29186aa18ee121217ab84830ea0898af74e143))
* dhis2.conf support for apache doris ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* Enable Delete instance playbook delete proxy include line for nginx ([845dc86](https://github.com/dhis2/dhis2-server-tools/commit/845dc86b0e2e813e659a4696c2de9d76c66df745))
* Enforing hostssl in pg_hba.conf ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* fix permissions for generated backup files with umask ([15a310e](https://github.com/dhis2/dhis2-server-tools/commit/15a310ef4c595e2dcb396ce0aacf5781d7edcd96))
* Grafana location configs on apache2 ([b13ddf1](https://github.com/dhis2/dhis2-server-tools/commit/b13ddf1bcebb1571234677ff728046a81f9ec645))
* Grafana/Prometheus monitoring support ([#60](https://github.com/dhis2/dhis2-server-tools/issues/60)) ([15a310e](https://github.com/dhis2/dhis2-server-tools/commit/15a310ef4c595e2dcb396ce0aacf5781d7edcd96))
* Implement nginx perf log ([ae403cd](https://github.com/dhis2/dhis2-server-tools/commit/ae403cdbb1ec958cb886ae65b51c4023faed165b))
* Implement Nginx perf logging ([f0e04b1](https://github.com/dhis2/dhis2-server-tools/commit/f0e04b1aa33ce0ef5a46105a63cfe5d6f7513149))
* Implement Nginx perf logging ([bd8c08a](https://github.com/dhis2/dhis2-server-tools/commit/bd8c08ae4454b9063221d9a0a13e7d9d4f3bf638))
* Optimize_LXD_for_production_setups ([08991ca](https://github.com/dhis2/dhis2-server-tools/commit/08991ca2077d1d1a5165f474f84179192a564cf0))
* prometheus/grafana firewall configs ([d14562f](https://github.com/dhis2/dhis2-server-tools/commit/d14562f54738b6bc5dcd6784371cb9fadf523cc5))
* prometheus/grafana monitoring ([ac7f387](https://github.com/dhis2/dhis2-server-tools/commit/ac7f3878b111e753ba91d694db582857ec4bd82e))
* support for static configuration files ([15a310e](https://github.com/dhis2/dhis2-server-tools/commit/15a310ef4c595e2dcb396ce0aacf5781d7edcd96))
* Validate `dhis2_version` input ([eab476b](https://github.com/dhis2/dhis2-server-tools/commit/eab476b1137af14a5f574059057106b7d0cbad2d))
* Validate `dhis2_version` input ([e8a155b](https://github.com/dhis2/dhis2-server-tools/commit/e8a155bb42dc117e00c06de39ec690c0f8b43816))
* Validate `dhis2_version` input ([3419473](https://github.com/dhis2/dhis2-server-tools/commit/34194739cfd6f291e9dfe1251649848da6959de2))
* Validate `dhis2_version` input ([9ddb05a](https://github.com/dhis2/dhis2-server-tools/commit/9ddb05a85eab07329543661741508b518dc212e7))


### 🐛 Bug Fixes

* add roles/backups/files/ssh/dhis2-restoredb script ([466796b](https://github.com/dhis2/dhis2-server-tools/commit/466796bfb6d9e91dd6d4451a7cbdb7e90e67a1dc))
* added sshpass needed in case of password auth to the managed hosts ([cfaaed0](https://github.com/dhis2/dhis2-server-tools/commit/cfaaed03920c80eb8a77388a9652f3d698fb15dc))
* broken instance DB server configuration, ([d52751b](https://github.com/dhis2/dhis2-server-tools/commit/d52751bce0803b119af9075ed9f3bdd7db6897c0))
* configuring postgresql firewall for apache doris connect ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* configuring postgresql pg_hba.conf for apache doris connect ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* distributed install OS checking ([5ed54a6](https://github.com/dhis2/dhis2-server-tools/commit/5ed54a6354c1906309feb65d6418883fe86c183c))
* Distributed install restoredb script ([5ed54a6](https://github.com/dhis2/dhis2-server-tools/commit/5ed54a6354c1906309feb65d6418883fe86c183c))
* ensure db_password files are owned by user running playbook ([fc7e799](https://github.com/dhis2/dhis2-server-tools/commit/fc7e799f8d3b8efb94b0bbd61dacb91778ce84b7))
* ensure dhis2.war push from the file system works ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* ensure munin agent is listening on host lxd ip, not 0.0.0.0 ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* Fix breaking changes for ansible 2.19 ([e373d7f](https://github.com/dhis2/dhis2-server-tools/commit/e373d7f3e631c26bc9a82c2dc7f652c1eb894b39))
* handle d-bus not ready error after LXD container creation ([b5b09fe](https://github.com/dhis2/dhis2-server-tools/commit/b5b09fe206b040ec5431afb8df8b5c2cfffa4524))
* include new host in munin server hosts when targeting create-instance tag ([845dc86](https://github.com/dhis2/dhis2-server-tools/commit/845dc86b0e2e813e659a4696c2de9d76c66df745))
* issues related to distributed install ([f7555fb](https://github.com/dhis2/dhis2-server-tools/commit/f7555fbca76b2bf795106c034090306ba5365bf5))
* Open port 8080 on DHIS2 instances, access from Prometheus/Grafana ([ffa4ce2](https://github.com/dhis2/dhis2-server-tools/commit/ffa4ce23cc8e0542fe474600de309a06792f2ae7))
* postgres_exporter unable to connect to the database ([7c89dbf](https://github.com/dhis2/dhis2-server-tools/commit/7c89dbf7d2746bffdb5e6eb9c9291547622da3df))
* remove antsibull changelog job ([#50](https://github.com/dhis2/dhis2-server-tools/issues/50)) ([d37db60](https://github.com/dhis2/dhis2-server-tools/commit/d37db60497e70c897296e1f1d548480c2a9d0160))
* remove apache_doris config parameter on inventory_hosts template ([0d12abf](https://github.com/dhis2/dhis2-server-tools/commit/0d12abf7001a23be8592c9310b4c2bd1ded990b6))
* Selecting the right apache_doris_host from hostvars ([7d70ebd](https://github.com/dhis2/dhis2-server-tools/commit/7d70ebd0094525b105936839cdc9fd931622dfbb))
* Set correct path for apache2 config ([0b66c79](https://github.com/dhis2/dhis2-server-tools/commit/0b66c7964ff021823504a599a63d40ff58cbbfe2))
* setting the JAVA_HOME based on the OS Architecture ([479211f](https://github.com/dhis2/dhis2-server-tools/commit/479211fe0065a5e1371c215a812d2eb677fd7833))
* setting the right name for nginx static conf ([95a26e6](https://github.com/dhis2/dhis2-server-tools/commit/95a26e62dc957f67ee4b077a47707ec22c3a1897))


### 📚 Documentation

* Adden doumentation onpostgreSQL and Proxy custom configs ([2701c25](https://github.com/dhis2/dhis2-server-tools/commit/2701c258808d228c678a0a67c953b66328eb141b))
* Custom Support for custom configs, PostgreSQL Apache2 and nginx ([ac7f387](https://github.com/dhis2/dhis2-server-tools/commit/ac7f3878b111e753ba91d694db582857ec4bd82e))

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
