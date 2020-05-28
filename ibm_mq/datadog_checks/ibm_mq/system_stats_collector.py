# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

try:
    import pymqi
except ImportError:
    pymqi = None


class SystemStatsCollector:
    """
    Collects metrics from the SYSTEM.ADMIN.STATISTICS.QUEUE
    See: https://www.ibm.com/support/knowledgecenter/en/SSFKSJ_9.0.0/com.ibm.mq.mon.doc/q037320_.htm
    """
    STATS_QUEUE = 'SYSTEM.ADMIN.STATISTICS.QUEUE'

    def __init__(self, config, gauge, log):
        self.config = config
        self.log = log
        self.gauge = gauge

    def collect_system_stats(self, queue_manager):
        queue = pymqi.Queue(queue_manager, self.STATS_QUEUE)
        try:
            while True:
                message = queue.get()
                self.log.debug(str(message))
                #process message
        except pymqi.MQMIError as e:
            if e.reason != pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                raise e
        finally:
            queue.close()

'''
MQI statistics messages
    MQI statistics messages contain information relating to the number of MQI calls made during a configured interval.
    For example, the information can include the number of MQI calls issued by a queue manager.

Queue statistics messages
    Queue statistics messages contain information relating to the activity of a queue during a configured interval.
    The information includes the number of messages put on, and retrieved from, the queue, and the total number of bytes
    processed by a queue.
    Each queue statistics message can contain up to 100 records, with each record relating to the activity per queue for
    which statistics were collected.

    Statistics messages are recorded only for local queues. If an application makes an MQI call against an alias queue,
    the statistics data is recorded against the base queue, and, for a remote queue, the statistics data is recorded
    against the transmission queue.

Channel statistics messages
    Channel statistics messages contain information relating to the activity of a channel during a configured interval. For example the information might be the number of messages transferred by the channel, or the number of bytes transferred by the channel.
    Each channel statistics message contains up to 100 records, with each record relating to the activity per channel for which statistics were collected.
'''