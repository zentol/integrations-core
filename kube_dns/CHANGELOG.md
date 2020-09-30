# CHANGELOG - Kube-dns

## 2.4.1 / 2020-06-29 / Agent 7.21.0

* [Fixed] Use agent 6 signature. See [#6907](https://github.com/DataDog/integrations-core/pull/6907).

## 2.4.0 / 2020-05-17 / Agent 7.20.0

* [Added] Allow optional dependency installation for all checks. See [#6589](https://github.com/DataDog/integrations-core/pull/6589).

## 2.3.1 / 2020-04-04 / Agent 7.19.0

* [Fixed] Update deprecated imports. See [#6088](https://github.com/DataDog/integrations-core/pull/6088).

## 2.3.0 / 2019-05-14 / Agent 6.12.0

* [Added] Adhere to code style. See [#3528](https://github.com/DataDog/integrations-core/pull/3528).

## 2.2.0 / 2019-03-29 / Agent 6.11.0

* [Added] Upgrade protobuf to 3.7.0. See [#3272](https://github.com/DataDog/integrations-core/pull/3272).

## 2.1.0 / 2019-02-18 / Agent 6.10.0

* [Fixed] Fix growing CPU and memory usage. See [#3066](https://github.com/DataDog/integrations-core/pull/3066).
* [Added] Support Python 3. See [#2896](https://github.com/DataDog/integrations-core/pull/2896).

## 2.0.1 / 2018-10-12 / Agent 6.6.0

* [Fixed] Submit metrics with instance tags. See [#2299](https://github.com/DataDog/integrations-core/pull/2299).

## 2.0.0 / 2018-09-04 / Agent 6.5.0

* [Changed] Update kube_dns to use the new OpenMetricsBaseCheck. See [#1980](https://github.com/DataDog/integrations-core/pull/1980).
* [Added] Limit Prometheus/OpenMetrics checks to 2000 metrics per run by default. See [#2093](https://github.com/DataDog/integrations-core/pull/2093).
* [Added] Make HTTP request timeout configurable in prometheus checks. See [#1790](https://github.com/DataDog/integrations-core/pull/1790).
* [Fixed] Add data files to the wheel package. See [#1727](https://github.com/DataDog/integrations-core/pull/1727).

## 1.4.0 / 2018-06-13 / Agent 6.4.0

* [Added] Package `auto_conf.yaml` for appropriate integrations. See [#1664](https://github.com/DataDog/integrations-core/pull/1664).

## 1.3.0 / 2018-05-11

* [IMPROVEMENT] Add metrics `kubedns.request_count.count`, `kubedns.error_count.count` and `cachemiss_count.count`, alternative metrics submitted as monotonic\_counts. See [#1341](https://github.com/DataDog/integrations-core/issues/1341)

## 1.2.0 / 2018-01-10

* [IMPROVEMENT] Bumping protobuf to version 3.5.1. See [#965](https://github.com/DataDog/integrations-core/issues/965)

## 1.1.0 / 2017-11-21

* [UPDATE] Update auto\_conf template to support agent 6 and 5.20+. See [#860](https://github.com/DataDog/integrations-core/issues/860)

## 1.0.0 / 2017-07-18

* [FEATURE] Add kube-dns integration, based on new PrometheusCheck class. See [#410](https://github.com/DataDog/integrations-core/issues/410) and [#451](https://github.com/DataDog/integrations-core/issues/451), thanks [@aerostitch](https://github.com/aerostitch)
