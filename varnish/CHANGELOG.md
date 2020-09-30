# CHANGELOG - varnish

## 1.8.0 / 2020-09-21

* [Added] Add config spec for varnish. See [#7538](https://github.com/DataDog/integrations-core/pull/7538).
* [Fixed] Fix style for the latest release of Black. See [#7438](https://github.com/DataDog/integrations-core/pull/7438).

## 1.7.0 / 2020-05-17 / Agent 7.20.0

* [Added] Allow optional dependency installation for all checks. See [#6589](https://github.com/DataDog/integrations-core/pull/6589).

## 1.6.1 / 2020-04-04 / Agent 7.19.0

* [Fixed] Update deprecated imports. See [#6088](https://github.com/DataDog/integrations-core/pull/6088).
* [Fixed] Remove logs sourcecategory. See [#6121](https://github.com/DataDog/integrations-core/pull/6121).

## 1.6.0 / 2020-01-13 / Agent 7.17.0

* [Added] Use lazy logging format. See [#5377](https://github.com/DataDog/integrations-core/pull/5377).

## 1.5.0 / 2019-12-02 / Agent 7.16.0

* [Fixed] Remove shlex. See [#5065](https://github.com/DataDog/integrations-core/pull/5065).
* [Added] Add version metadata. See [#4952](https://github.com/DataDog/integrations-core/pull/4952).

## 1.4.0 / 2019-05-14 / Agent 6.12.0

* [Added] Adhere to code style. See [#3579](https://github.com/DataDog/integrations-core/pull/3579).

## 1.3.1 / 2019-03-29 / Agent 6.11.0

* [Fixed] ensure_unicode with normalize for py3 compatibility. See [#3218](https://github.com/DataDog/integrations-core/pull/3218).

## 1.3.0 / 2019-01-04 / Agent 6.9.0

* [Added] Support Python 3. See [#2810](https://github.com/DataDog/integrations-core/pull/2810).

## 1.2.1 / 2018-09-04 / Agent 6.5.0

* [Fixed] Make sure all checks' versions are exposed. See [#1945](https://github.com/DataDog/integrations-core/pull/1945).
* [Fixed] Add data files to the wheel package. See [#1727](https://github.com/DataDog/integrations-core/pull/1727).

## 1.2.0 / 2018-05-11

* [IMPROVEMENT] Add custom tag support for service checks.

## 1.1.2 / 2018-03-23

* [IMPROVEMENT] Add support for collecting varnishadm service checks for Varnish 5. See [#1130](https://github.com/DataDog/integrations-core/issues/1130).

## 1.1.1 / 2018-02-13

* [DOC] Adding configuration for log collection in `conf.yaml`

## 1.1.0 / 2018-01-10

* [IMPROVEMENT] Use JSON with varnishstat starting varnish 5.0.0. See [#939](https://github.com/DataDog/integrations-core/pull/939).

## 1.0.6 2017-11-21

* [BUGFIX] Fixes pulling backend service check when its manually overriden.

## 1.0.5 2017-10-10

* [BUGFIX] Fixes broken service check behavior. See [#795](https://github.com/DataDog/integrations-core/issues/795).
* [BUGFIX] Fix `varnishadm backend.list -p` parsing for newer versions of Varnish. See [#739](https://github.com/DataDog/integrations-core/issues/739). (Thanks [@philipseidel](https://github.com/philipseidel))

## 1.0.4 2017-08-28

* [IMPROVEMENT] Support for passing additional parameters to varnishstat and varnishadm in order to better support service discovery. See [#498](https://github.com/DataDog/integrations-core/issues/498), thanks [@philipseidel][9]

## 1.0.3 / 2017-07-18

* [BUGFIX] Fixes an issue with retrieving the backend service checks. Special thanks to [@adongy](https://github.com/adongy) for finding this! [#582](https://github.com/DataDog/integrations-core/issues/582)

## 1.0.2 / 2017-07-18

* [IMPROVEMENT] adds ability to filter metrics using the -f option of varnishstat. See [#361](https://github.com/DataDog/integrations-core/issues/361)

## 1.0.1 / 2017-06-05

* [IMPROVEMENT] Support varnish 4.1 for the service check using varnishadm. See [#360](https://github.com/DataDog/integrations-core/issues/360)

## 1.0.0 / 2017-03-22

* [FEATURE] adds varnish integration.
