# Source and license

**Olist and André Sionek: Brazilian E-Commerce Public Dataset by Olist**

- [Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Kaggle metadata endpoint](https://www.kaggle.com/api/v1/datasets/view/olistbr/brazilian-ecommerce)
- [Public download endpoint](https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce)
- Retrieved 16 October 2026. Source records describe historical purchases in 2016–2018.
- Archive: 44,717,580 bytes. SHA-256:
  `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`.
- Kaggle metadata identifies the license as
  [Creative Commons Attribution-NonCommercial-ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

The source dataset and data-derived CSVs, database, report data, dashboard exports,
and figures retain **CC BY-NC-SA 4.0** attribution and share-alike conditions.
This portfolio demonstration is noncommercial. Do not reuse this dataset in a
paid client deliverable without an appropriate separate right or permission.
The reusable original Python/SQL/report-authoring code is MIT licensed; that does
not relicense source records or imply unrestricted commercial use of the sample.

Changes: selected six related tables, removed unnecessary personal/location detail,
validated keys, standardized labels, calculated order/item metrics, translated
categories using the supplied mapping, and added quality/exception exports.
Source CSVs are not edited. Per-file hashes and row counts live in each processed
snapshot's `manifest.json`; the original Kaggle metadata is saved alongside this file.

The source description explains that an order may contain multiple items and
multiple sellers. This report preserves item rows and aggregates payments before
joining. It is an independent educational portfolio case study, not commissioned
work for Olist or Albertsons. Historical observations do not represent current
delivery performance or a live unfulfilled-order queue.
