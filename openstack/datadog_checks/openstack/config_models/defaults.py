# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.base.utils.models.fields import get_default_field_value


def shared_exclude_network_ids(field, value):
    return get_default_field_value(field, value)


def shared_exclude_server_ids(field, value):
    return get_default_field_value(field, value)


def shared_hypervisor_ids(field, value):
    return get_default_field_value(field, value)


def shared_nova_api_version(field, value):
    return 'v2.1'


def shared_os_host(field, value):
    return get_default_field_value(field, value)


def shared_service(field, value):
    return get_default_field_value(field, value)


def shared_ssl_verify(field, value):
    return True


def shared_use_agent_proxy(field, value):
    return True


def instance_append_tenant_id(field, value):
    return False


def instance_auth_scope(field, value):
    return get_default_field_value(field, value)


def instance_collect_all_projects(field, value):
    return True


def instance_empty_default_hostname(field, value):
    return False


def instance_min_collection_interval(field, value):
    return 15


def instance_service(field, value):
    return get_default_field_value(field, value)


def instance_tags(field, value):
    return get_default_field_value(field, value)
