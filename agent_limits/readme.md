## Using docker image

```
ddev env start snmp py38-python_ad -e DD_SITE=datad0g.com -e DD_API_KEY=$DD_API_KEY -e DD_TAGS=env:alex-snmp

docker cp 'agent_limits/snmp_confd/snmp_conf_2k.yaml' 'dd_snmp_py38-python_ad:/etc/datadog-agent/conf.d/snmp.d/snmp.yaml'

docker cp 'agent_limits/datadog.yaml' 'dd_snmp_py38-python_ad:/etc/datadog-agent/datadog.yaml'
docker cp 'agent_limits/openmetrics.d/conf.yaml' 'dd_snmp_py38-python_ad:/etc/datadog-agent/conf.d/openmetrics.d/conf.yaml'

docker restart dd_snmp_py38-python_ad
```


```shell
ddev env start snmp py38-python_ad -e DD_SITE=datad0g.com -e DD_API_KEY=$DD_API_KEY_STAGING -e 'DD_CHECK_RUNNERS=1000' -e DD_TAGS="env:alex-snmp test_run:$(date --iso-8601=minutes)"
```

