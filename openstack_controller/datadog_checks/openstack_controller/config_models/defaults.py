# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.base.utils.models.fields import get_default_field_value


def shared_proxy(field, value):
    return get_default_field_value(field, value)


def shared_service(field, value):
    return get_default_field_value(field, value)


def shared_skip_proxy(field, value):
    return False


def shared_timeout(field, value):
    return 10


def instance_auth_token(field, value):
    return get_default_field_value(field, value)


def instance_auth_type(field, value):
    return 'basic'


def instance_aws_host(field, value):
    return get_default_field_value(field, value)


def instance_aws_region(field, value):
    return get_default_field_value(field, value)


def instance_aws_service(field, value):
    return get_default_field_value(field, value)


def instance_blacklist_project_names(field, value):
    return get_default_field_value(field, value)


def instance_collect_hypervisor_load(field, value):
    return True


def instance_collect_hypervisor_metrics(field, value):
    return True


def instance_collect_network_metrics(field, value):
    return True


def instance_collect_project_metrics(field, value):
    return True


def instance_collect_server_diagnostic_metrics(field, value):
    return True


def instance_collect_server_flavor_metrics(field, value):
    return True


def instance_connect_timeout(field, value):
    return get_default_field_value(field, value)


def instance_empty_default_hostname(field, value):
    return False


def instance_exclude_network_ids(field, value):
    return get_default_field_value(field, value)


def instance_exclude_server_ids(field, value):
    return get_default_field_value(field, value)


def instance_extra_headers(field, value):
    return get_default_field_value(field, value)


def instance_headers(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_auth(field, value):
    return 'disabled'


def instance_kerberos_cache(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_delegate(field, value):
    return False


def instance_kerberos_force_initiate(field, value):
    return False


def instance_kerberos_hostname(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_keytab(field, value):
    return get_default_field_value(field, value)


def instance_kerberos_principal(field, value):
    return get_default_field_value(field, value)


def instance_keystone_server_url(field, value):
    return 'https://<KEYSTONE_ENDPOINT>:<PORT>/'


def instance_log_requests(field, value):
    return False


def instance_min_collection_interval(field, value):
    return 15


def instance_ntlm_domain(field, value):
    return get_default_field_value(field, value)


def instance_openstack_cloud_name(field, value):
    return get_default_field_value(field, value)


def instance_openstack_config_file_path(field, value):
    return get_default_field_value(field, value)


def instance_paginated_limit(field, value):
    return 1000


def instance_password(field, value):
    return get_default_field_value(field, value)


def instance_persist_connections(field, value):
    return False


def instance_proxy(field, value):
    return get_default_field_value(field, value)


def instance_read_timeout(field, value):
    return get_default_field_value(field, value)


def instance_service(field, value):
    return get_default_field_value(field, value)


def instance_skip_proxy(field, value):
    return False


def instance_tags(field, value):
    return get_default_field_value(field, value)


def instance_timeout(field, value):
    return 10


def instance_tls_ca_cert(field, value):
    return get_default_field_value(field, value)


def instance_tls_cert(field, value):
    return get_default_field_value(field, value)


def instance_tls_ignore_warning(field, value):
    return False


def instance_tls_private_key(field, value):
    return get_default_field_value(field, value)


def instance_tls_use_host_header(field, value):
    return False


def instance_tls_verify(field, value):
    return True


def instance_use_agent_proxy(field, value):
    return True


def instance_use_legacy_auth_encoding(field, value):
    return True


def instance_use_shortname(field, value):
    return False


def instance_username(field, value):
    return get_default_field_value(field, value)


def instance_whitelist_project_names(field, value):
    return get_default_field_value(field, value)
