## [0.3.0](https://github.com/tvna/clairvoyance/compare/v0.2.0...v0.3.0) (2026-07-01)

### Features

* **adaptive-coaching:** add a session grace period before coaching ([93fa0be](https://github.com/tvna/clairvoyance/commit/93fa0bece695a6bfae945e36dd3908f5a023ef23))
* **adaptive-coaching:** back the store with the sqlite3 CLI, python fallback ([28db378](https://github.com/tvna/clairvoyance/commit/28db378de766c4bd8c7611921f95fae2caf8fad3))
* **adaptive-coaching:** coach a person's adaptive challenge with a local-gated quiz ([f1bd7e1](https://github.com/tvna/clairvoyance/commit/f1bd7e13804482b6a963781cd374d708755f705a))
* **adaptive-coaching:** improve learning loop refs [#34](https://github.com/tvna/clairvoyance/issues/34) ([f60677b](https://github.com/tvna/clairvoyance/commit/f60677bba4bc80196aa93ebf957b3ec2e11f0177))
* **adaptive-store:** opt-in context capture with redaction and rotation ([2bba05c](https://github.com/tvna/clairvoyance/commit/2bba05c8f540c861f9655c248d619eb191804df6))
* **battle:** add baseline ablation mode to measure skill lift ([1512fb6](https://github.com/tvna/clairvoyance/commit/1512fb607fbffeb73f1304a65d59a3eb45e3e503))
* **human-harness:** make the confirmation a decision-ready handoff ([a5ad3d7](https://github.com/tvna/clairvoyance/commit/a5ad3d711adc63a23a533c15b3ed88a92f8f40f1))
* **skills:** add human-harness skill ([271f648](https://github.com/tvna/clairvoyance/commit/271f64835ab10ca0b5813f840ad366cc4d312050))
* **skills:** measure skill maturity across deterministic + probabilistic lanes ([da69336](https://github.com/tvna/clairvoyance/commit/da6933639ed9db6e67bae1307d005c94b55764a5))

### Bug Fixes

* **adaptive-coaching:** resolve review findings on skill conflicts and store bugs ([a39f3a3](https://github.com/tvna/clairvoyance/commit/a39f3a3c65cd496afca2a209c5fc80f0c33b1578))
* **adaptive-coaching:** separate quiz and feedback phases refs [#34](https://github.com/tvna/clairvoyance/issues/34) ([05626da](https://github.com/tvna/clairvoyance/commit/05626da690aedaff37bd7e6d22154ac95532f7a8))
* **adaptive-store:** read raw context from stdin; add Windows CI ([0209bc2](https://github.com/tvna/clairvoyance/commit/0209bc28e57a950674e50ebeebcef76a41ebf4c8))
* **adaptive-store:** require --category on record across both backends ([dacdca4](https://github.com/tvna/clairvoyance/commit/dacdca45d26f4519a7866886b5331f23212c7155)), closes [#17](https://github.com/tvna/clairvoyance/issues/17)
* **check-skills:** UTF-8 I/O, tighter XML match, reuse link scanner ([034a8c9](https://github.com/tvna/clairvoyance/commit/034a8c9344fae828976075a0169819c8d67c6115))
* **ci:** don't delete the sync branch while it has an open PR ([54e1010](https://github.com/tvna/clairvoyance/commit/54e1010893e9d9d908e67909e6fe58e2e258a579)), closes [#33](https://github.com/tvna/clairvoyance/issues/33)
* **ci:** scope sync-bot App secrets to a GitHub Environment ([06d4516](https://github.com/tvna/clairvoyance/commit/06d45166fd5f1443abbd04ff99803125b2547d6a))
* **ci:** sign sync-agent-instructions PR commits via a GitHub App token ([6272c72](https://github.com/tvna/clairvoyance/commit/6272c726e57f7d2410d6de4c5ef747e4439b51b4))
* **hooks:** fix operator language to an env var, drop unstable git-identity mapping ([8a6a8d8](https://github.com/tvna/clairvoyance/commit/8a6a8d896ec3e5ee51287350a11e77a9c837e79a)), closes [#30](https://github.com/tvna/clairvoyance/issues/30)
* **hooks:** keep personal emails out of the committed language mapping ([da269ae](https://github.com/tvna/clairvoyance/commit/da269ae70acc80365f461ef638d92e3b4ff09f33))
* **hooks:** make native-language handoff track the active contributor ([f8929ae](https://github.com/tvna/clairvoyance/commit/f8929ae6b7edf37d48d28711c2b77947d5a549aa))
* **hooks:** rank the legacy owner env below the contributor mapping ([3ca3d42](https://github.com/tvna/clairvoyance/commit/3ca3d42b0bc7b256ee9ffcbc5b31caf6973cc961))
* **hooks:** stop serving the owner's language to other contributors ([ef3cf9b](https://github.com/tvna/clairvoyance/commit/ef3cf9b2820ae9d7f0ce4bfc83da75d626960225))
* **hooks:** stop the legacy owner language from shadowing the question handoff ([00f5713](https://github.com/tvna/clairvoyance/commit/00f5713904b4ce6c3fea19290767018c38eb6c30)), closes [#25](https://github.com/tvna/clairvoyance/issues/25)
* **hooks:** track contributor language via a committed identity mapping ([f0f6757](https://github.com/tvna/clairvoyance/commit/f0f6757d9643a8231580fb259eecaa565b77dfa5))
* **human-harness:** do not let user overrides waive mandatory safety gates ([476277c](https://github.com/tvna/clairvoyance/commit/476277c9085d66444c21707a6f403e67381a58e3))
* **packaging:** flatten plugin to repo root so apm deploys skills ([f648180](https://github.com/tvna/clairvoyance/commit/f648180777d7eba6d2769112a42f5116aa45e8b9))

## [0.2.0](https://github.com/tvna/clairvoyance/compare/v0.1.0...v0.2.0) (2026-06-28)

### Features

* add Codex plugin alongside the Claude Code plugin ([d43ea3b](https://github.com/tvna/clairvoyance/commit/d43ea3bb9b20951e17eb0b28aefcd6a30b58a631))
