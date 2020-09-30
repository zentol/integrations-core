# CHANGELOG - Prometheus

## 3.3.0 / 2020-05-17 / Agent 7.20.0

* [Added] Allow optional dependency installation for all checks. See [#6589](https://github.com/DataDog/integrations-core/pull/6589).

## 3.2.1 / 2020-04-04 / Agent 7.19.0

* [Fixed] Update prometheus_client. See [#6200](https://github.com/DataDog/integrations-core/pull/6200).
* [Fixed] Update deprecated imports. See [#6088](https://github.com/DataDog/integrations-core/pull/6088).

## 3.2.0 / 2019-05-14 / Agent 6.12.0

* [Fixed] Fix type override values in example config. See [#3717](https://github.com/DataDog/integrations-core/pull/3717).
* [Added] Adhere to code style. See [#3560](https://github.com/DataDog/integrations-core/pull/3560).

## 3.1.0 / 2019-02-18 / Agent 6.10.0

* [Added] Support Python 3. See [#3048](https://github.com/DataDog/integrations-core/pull/3048).

## 3.0.1 / 2019-01-04 / Agent 6.9.0

* [Fixed] Added crucial words to make sentence clearer. See [#2811](https://github.com/DataDog/integrations-core/pull/2811). Thanks [someword](https://github.com/someword).
* [Fixed] Change the prometheus example to use prometheus_url. See [#2790](https://github.com/DataDog/integrations-core/pull/2790). Thanks [someword](https://github.com/someword).

## 3.0.0 / 2018-10-12 / Agent 6.6.0

* [Changed] Change default prometheus metric limit to 2000. See [#2248](https://github.com/DataDog/integrations-core/pull/2248).
* [Fixed] Temporarily increase the limit of prometheus metrics sent for 6.5. See [#2214](https://github.com/DataDog/integrations-core/pull/2214).

## 2.0.0 / 2018-09-04 / Agent 6.5.0

* [Added] Limit Prometheus/OpenMetrics checks to 2000 metrics per run by default. See [#2093](https://github.com/DataDog/integrations-core/pull/2093).
* [Fixed] Make sure all checks' versions are exposed. See [#1945](https://github.com/DataDog/integrations-core/pull/1945).
* [Changed] Bump prometheus client library to 0.3.0. See [#1866](https://github.com/DataDog/integrations-core/pull/1866).
* [Added] Make HTTP request timeout configurable in prometheus checks. See [#1790](https://github.com/DataDog/integrations-core/pull/1790).
* [Fixed] Add data files to the wheel package. See [#1727](https://github.com/DataDog/integrations-core/pull/1727).

## 1.0.0/ 2018-03-23

* [FEATURE] adds prometheus integration.
