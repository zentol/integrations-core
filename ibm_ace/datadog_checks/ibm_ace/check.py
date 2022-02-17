# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pymqi

from datadog_checks.base import AgentCheck

from .config_models import ConfigMixin


class IbmAceCheck(AgentCheck, ConfigMixin):
    __NAMESPACE__ = 'ibm_ace'

    def __init__(self, name, init_config, instances):
        super(IbmAceCheck, self).__init__(name, init_config, instances)

    def check(self, _):
        # self.collect()
        self.gauge('foo', 1)

    def collect(self):
        # https://www.ibm.com/docs/en/app-connect/12.0?topic=events-subscribing-event-message-topics
        channel_definition = pymqi.CD()
        channel_definition.ChannelName = 'DEV.ADMIN.SVRCONN'.encode('utf-8')
        channel_definition.ConnectionName = 'localhost(11414)'.encode('utf-8')
        channel_definition.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
        channel_definition.TransportType = pymqi.CMQC.MQXPT_TCP
        channel_definition.Version = getattr(pymqi.CMQC, 'MQCD_VERSION_6')

        connection_options = {'cd': channel_definition, 'user': 'admin', 'password': 'passw0rd'}

        queue_manager = pymqi.QueueManager(None)
        queue_manager.connect_with_options('QM1', **connection_options)

        sub_desc = pymqi.SD()
        sub_desc['Options'] = (
            pymqi.CMQC.MQSO_CREATE + pymqi.CMQC.MQSO_RESUME + pymqi.CMQC.MQSO_DURABLE + pymqi.CMQC.MQSO_MANAGED
        )
        sub_desc.set_vs('SubName', 'MySub')
        # sub_desc.set_vs('ObjectString', '$SYS/Broker/integration_server/Statistics/JSON/Resource/ACESERVER')
        # sub_desc.set_vs('ObjectString', '$SYS/Broker/+/Statistics/#')
        sub_desc.set_vs('ObjectString', '$SYS/Broker/+/ResourceStatistics/#')

        sub = pymqi.Subscription(queue_manager)
        sub.sub(sub_desc=sub_desc)

        get_opts = pymqi.GMO(
            Options=pymqi.CMQC.MQGMO_NO_SYNCPOINT + pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING + pymqi.CMQC.MQGMO_WAIT
        )
        get_opts['WaitInterval'] = 30000

        try:
            data = sub.get(None, pymqi.md(), get_opts)
            self.log.error('received data: %s' % data)
        finally:
            sub.close(sub_close_options=pymqi.CMQC.MQCO_KEEP_SUB, close_sub_queue=True)
            queue_manager.disconnect()
