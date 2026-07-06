## [0.5.0](https://github.com/tvna/clairvoyance/compare/v0.4.0...v0.5.0) (2026-07-06)

### Features

* **hooks:** reinforce operator language on every turn ([#116](https://github.com/tvna/clairvoyance/issues/116)) ([#117](https://github.com/tvna/clairvoyance/issues/117)) ([bcc8701](https://github.com/tvna/clairvoyance/commit/bcc8701feccd0947da6a1236511705fd04fcf895))

### Bug Fixes

* **adaptive-store:** require recurring, session-spanning signal for readiness (Refs [#89](https://github.com/tvna/clairvoyance/issues/89)) ([#122](https://github.com/tvna/clairvoyance/issues/122)) ([af8e48c](https://github.com/tvna/clairvoyance/commit/af8e48c842a2c1de5c11a5adcdb6aac60bd7cf44)), closes [F1/#93](https://github.com/F1/clairvoyance/issues/93)
* **battle:** harden _claude() against CLI crash/timeout/malformed output ([#111](https://github.com/tvna/clairvoyance/issues/111)) ([#115](https://github.com/tvna/clairvoyance/issues/115)) ([461613a](https://github.com/tvna/clairvoyance/commit/461613ac0d97cfc2ab9bdbc5210685237cc23c85)), closes [#104](https://github.com/tvna/clairvoyance/issues/104)
* **hooks:** nest UserPromptSubmit additionalContext under hookSpecificOutput (Closes [#119](https://github.com/tvna/clairvoyance/issues/119)) ([#120](https://github.com/tvna/clairvoyance/issues/120)) ([f6df2a6](https://github.com/tvna/clairvoyance/commit/f6df2a6fceb782437969a788c8fe41d01e44490c)), closes [116/#117](https://github.com/116/clairvoyance/issues/117)

## [0.4.0](https://github.com/tvna/clairvoyance/compare/v0.3.0...v0.4.0) (2026-07-05)

### Features

* **battle:** classify CLI infra errors separately from content failures ([#101](https://github.com/tvna/clairvoyance/issues/101)) ([#104](https://github.com/tvna/clairvoyance/issues/104)) ([e9f003b](https://github.com/tvna/clairvoyance/commit/e9f003b86088a238bf6d701bda2cbc3848b81de4))
* **managed:** add local dev compose with Keycloak IdP ([e483d6b](https://github.com/tvna/clairvoyance/commit/e483d6b4d6e41a30d5df83c13725ef05228255ea)), closes [#77](https://github.com/tvna/clairvoyance/issues/77)
* **managed:** add search, paging, time filter, and review dismissal to admin API ([cfa6c0e](https://github.com/tvna/clairvoyance/commit/cfa6c0ecd6c4acfab1c63c1445ba316ead1f9128)), closes [#68](https://github.com/tvna/clairvoyance/issues/68)
* **managed:** add the admin API zod contract layer and fetch client ([7ef0c96](https://github.com/tvna/clairvoyance/commit/7ef0c9629f49dc4a8c16a72c5cce92f3ba6966b7)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** add the E2E harness and managed-ui-e2e CI smoke job ([d7ccca2](https://github.com/tvna/clairvoyance/commit/d7ccca205d74ddbd566a7d91dfc6be2b23d62bef)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** build the 5 admin screens, layout, and shared components ([4914dbf](https://github.com/tvna/clairvoyance/commit/4914dbf8b94e358a249ce87df9b3e4d8ce55c098)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** build the ui image and add its compose service ([4829897](https://github.com/tvna/clairvoyance/commit/48298973bae084f8581bc59b6e198abfa11562c7)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** initial managed coaching server refs [#51](https://github.com/tvna/clairvoyance/issues/51) ([c10cee4](https://github.com/tvna/clairvoyance/commit/c10cee45a874d1921956882c90406feaa76109f4))
* **managed:** replace admin UI gap workarounds with the new API surface ([8e68d7d](https://github.com/tvna/clairvoyance/commit/8e68d7d08896185a8472c6716b779fcc82a9b4e0)), closes [#68](https://github.com/tvna/clairvoyance/issues/68)
* **managed:** scaffold the admin UI npm project and CI gates ([02cf99d](https://github.com/tvna/clairvoyance/commit/02cf99dcac991ab2f77a4795965b4d4998ff8edf)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** wire OIDC authentication for the admin UI ([33461d8](https://github.com/tvna/clairvoyance/commit/33461d82df346696a1205c5ab13c93cb4ece4456)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **scripts:** ban the Claude Code rules lane deterministically refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([cb45ab2](https://github.com/tvna/clairvoyance/commit/cb45ab26828d30447dd807e92da00fd2f71cd6ae))
* **scripts:** gate README listings and language-rule wording refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([cdab4e2](https://github.com/tvna/clairvoyance/commit/cdab4e2b18ee4da0fcef63ed7b32d79c601e8763))
* **session-handoff:** decide whether the Fable-optimized path applies ([c6863f9](https://github.com/tvna/clairvoyance/commit/c6863f94cdd1820314a1dbbee444f3a9802a1185)), closes [#81](https://github.com/tvna/clairvoyance/issues/81)
* **session-handoff:** emit a Fable-optimized handoff for Fable sessions ([0e9cff3](https://github.com/tvna/clairvoyance/commit/0e9cff3819f1025531f0cb5a7bba9bd287c19a88)), closes [#81](https://github.com/tvna/clairvoyance/issues/81)
* **session-handoff:** label the Fable handoff and degrade safely to Opus ([237a764](https://github.com/tvna/clairvoyance/commit/237a764620dbb315cca4439e26b75a870bb5963a)), closes [#81](https://github.com/tvna/clairvoyance/issues/81)
* **visual-handoff:** add opt-in visualization skill refs [#44](https://github.com/tvna/clairvoyance/issues/44) ([e472bf1](https://github.com/tvna/clairvoyance/commit/e472bf11054419c40b6a40ae88c6f871c563bd51))

### Bug Fixes

* **adaptive-coaching:** align trigger wording and restore smaller-next-step option ([#99](https://github.com/tvna/clairvoyance/issues/99)) ([3632c7b](https://github.com/tvna/clairvoyance/commit/3632c7bd69fb2fe9581390d9fb5e583e66909230))
* **adaptive-coaching:** keep trait labels and confidence verdicts out of pre-answer output ([6eddd2f](https://github.com/tvna/clairvoyance/commit/6eddd2f91dfa7a8b1d74a541ab1f140e27981b2c)), closes [#69](https://github.com/tvna/clairvoyance/issues/69)
* **adaptive-coaching:** open with heat-lowering when the person fears judgement ([#99](https://github.com/tvna/clairvoyance/issues/99)) ([9dc1f6f](https://github.com/tvna/clairvoyance/commit/9dc1f6fa47bd77209adaaed076720f2caf57cfeb))
* **adaptive-store:** bash-3.2-safe quoting, prune on status, warn on misconfig ([583e0c2](https://github.com/tvna/clairvoyance/commit/583e0c2b8dd3aafc8b1a68f90e7f6662a93e4ef6)), closes [#89](https://github.com/tvna/clairvoyance/issues/89) [#89](https://github.com/tvna/clairvoyance/issues/89)
* **adaptive-store:** evict outcome rows before raw signal on count rotation ([63eeec3](https://github.com/tvna/clairvoyance/commit/63eeec330bdec0e8c32f256aab479c0f599b6073)), closes [#102](https://github.com/tvna/clairvoyance/issues/102) [#89](https://github.com/tvna/clairvoyance/issues/89)
* **adaptive-store:** exclude quiz-outcome rows from readiness (F4, option B) ([62897b6](https://github.com/tvna/clairvoyance/commit/62897b6e63d35d1e5214466aac3f98760c36340d)), closes [#89](https://github.com/tvna/clairvoyance/issues/89) [#89](https://github.com/tvna/clairvoyance/issues/89)
* **adaptive-store:** serve readable data when status cannot prune ([4de1f8c](https://github.com/tvna/clairvoyance/commit/4de1f8cbd2f4ac99ea5bfe1f9a17af8d200f3a75)), closes [#93](https://github.com/tvna/clairvoyance/issues/93)
* **managed:** add a stable tiebreaker to reviews/due pagination ([d860137](https://github.com/tvna/clairvoyance/commit/d8601373da0b35ad968d0990eb507922c37a7947))
* **managed:** address review feedback refs [#51](https://github.com/tvna/clairvoyance/issues/51) ([3ac0b1b](https://github.com/tvna/clairvoyance/commit/3ac0b1b9c436b4e52fb56bda2a412fe086b7bb55))
* **managed:** apply code-review findings to the admin UI ([6552c31](https://github.com/tvna/clairvoyance/commit/6552c314db22e00627dc513dccc3516775542d34)), closes [#61](https://github.com/tvna/clairvoyance/issues/61) [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** apply self-review findings before PR refs [#51](https://github.com/tvna/clairvoyance/issues/51) ([df38b31](https://github.com/tvna/clairvoyance/commit/df38b316e4b831e9b843605a64e8ea9f560fbd0c))
* **managed:** bind dev compose ports to loopback ([3dd19ce](https://github.com/tvna/clairvoyance/commit/3dd19ce3ae28a2ee7214f46769029f9a0e5019ec)), closes [#77](https://github.com/tvna/clairvoyance/issues/77)
* **managed:** clear the query cache when a session ends ([ec14e29](https://github.com/tvna/clairvoyance/commit/ec14e299a1a138addfd5da0fb1f8b5bfa96517b1)), closes [#63](https://github.com/tvna/clairvoyance/issues/63) [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** correct dev compose review findings ([f5054a3](https://github.com/tvna/clairvoyance/commit/f5054a3da8420cf53e7359302248c4643be85600)), closes [#77](https://github.com/tvna/clairvoyance/issues/77)
* **managed:** fix E2E sign-in redirect and discovery-absent overrides ([80a230e](https://github.com/tvna/clairvoyance/commit/80a230e80e23a6af1b99dfc6282c98e8926dc2b7)), closes [#61](https://github.com/tvna/clairvoyance/issues/61) [#59](https://github.com/tvna/clairvoyance/issues/59)
* **managed:** harden the managed version regex against parens in FastAPI args ([5d4bf83](https://github.com/tvna/clairvoyance/commit/5d4bf83c85d10dc325610be6f0afebbfeb08f0f6))
* **managed:** normalize audit-log time bounds to UTC ([0b02e71](https://github.com/tvna/clairvoyance/commit/0b02e719b5619e9f0244c1699657eff7932c3d26))
* **managed:** return to the originally requested route after sign-in ([e3af39f](https://github.com/tvna/clairvoyance/commit/e3af39f916289708f8dbf57d112f1e62c05af130)), closes [#59](https://github.com/tvna/clairvoyance/issues/59)
* **release:** order the managed no-release rule after the breaking rule ([3292111](https://github.com/tvna/clairvoyance/commit/3292111696c045a58f717ee6c650e00f3ed0e8c6)), closes [#71](https://github.com/tvna/clairvoyance/issues/71)
* **scripts:** match the exact README skill-table row, not a substring refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([b9ab7d2](https://github.com/tvna/clairvoyance/commit/b9ab7d232ca5bdcc844d4c5279299642fcfdc764))
* **session-handoff:** include Mythos in the operating-block self-guard ([45429ba](https://github.com/tvna/clairvoyance/commit/45429baac09da6ede47d7d94e863cb38835b50e5)), closes [#81](https://github.com/tvna/clairvoyance/issues/81)
* **skills:** add diagram labels to the localization enumeration refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([5d7e40e](https://github.com/tvna/clairvoyance/commit/5d7e40e98881d21d15a60cb9ecf8bd6807dc05eb))
* **skills:** close routing gaps surfaced by the maturity review refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([eeda03f](https://github.com/tvna/clairvoyance/commit/eeda03f9418ddade8700ea1da0adb9651985f060))
* **skills:** localize question bullet titles; make the hook the language rule's single carrier refs [#57](https://github.com/tvna/clairvoyance/issues/57) ([894e83d](https://github.com/tvna/clairvoyance/commit/894e83d4b91ab2c47ece0f8e825a5802d095401e))
* **visual-handoff:** layer visuals on the routed skill, not instead of it refs [#44](https://github.com/tvna/clairvoyance/issues/44) ([b3a7c77](https://github.com/tvna/clairvoyance/commit/b3a7c77fc860928bff362387b6bcb27b750248de)), closes [#45](https://github.com/tvna/clairvoyance/issues/45)

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
