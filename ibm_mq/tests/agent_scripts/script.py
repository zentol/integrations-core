import pymqi


# Modify this
CONFIG = {
    'channel': 'DEV.ADMIN.SVRCONN',
    'queue_manager': 'QM1',
    'host': 'localhost',
    'port': 11414,
    'username': 'admin',
    'password': 'passw0rd',
}


def main():
    displayed_config = dict(CONFIG)
    if 'password' in displayed_config:
        displayed_config['password'] = '*****'

    CONFIG.setdefault('convert_endianness', False)
    CONFIG.setdefault('timeout', 5)
    CONFIG.setdefault('mqcd_version', 6)
    timeout = int(float(CONFIG['timeout']) * 1000)

    print('<<< Environment >>>')
    print('-------------------')
    print(f'Config: {displayed_config}')
    queue_manager = get_queue_manager()

    print()
    print('<<< Metadata >>>')
    print('----------------')
    try:
        pcf = pymqi.PCFExecute(
            queue_manager, response_wait_interval=timeout, convert=CONFIG['convert_endianness']
        )
        response = pcf.MQCMD_INQUIRE_Q_MGR({pymqi.CMQCFC.MQIACF_Q_MGR_ATTRS: [pymqi.CMQC.MQCA_VERSION]})
    except Exception as e:
        print(f'Error getting version: {e}')
    else:
        raw_version = response[0][pymqi.CMQC.MQCA_VERSION].decode('utf-8')
        print(f'Version: {raw_version}')

    print()
    print('<<< Channels >>>')
    print('----------------')
    try:
        pcf = pymqi.PCFExecute(
            queue_manager, response_wait_interval=timeout, convert=CONFIG['convert_endianness']
        )
        response = pcf.MQCMD_INQUIRE_CHANNEL({pymqi.CMQCFC.MQCACH_CHANNEL_NAME: b'*'})
    except Exception as e:
        print(f'Error getting channels: {e}')
    else:
        print(f'Number of channels: {len(response)}')

        for channel_info in response:
            channel_name = channel_info[pymqi.CMQCFC.MQCACH_CHANNEL_NAME].strip().decode('utf-8')

            try:
                pcf = pymqi.PCFExecute(
                    queue_manager, response_wait_interval=timeout, convert=CONFIG['convert_endianness']
                )
                response = pcf.MQCMD_INQUIRE_CHANNEL_STATUS({pymqi.CMQCFC.MQCACH_CHANNEL_NAME: channel_name.encode('utf-8')})
            except Exception as e:
                print(f'{channel_name} | status: {e}')
            else:
                # Should only be one response
                for channel_info in response:
                    channel_status = CHANNEL_STATUSES.get(channel_info[pymqi.CMQCFC.MQIACH_CHANNEL_STATUS], 'UNKNOWN')
                    print(f'{channel_name} | status: {channel_status}')

    print()
    print('<<< Queues >>>')
    print('--------------')
    for queue_type_name, queue_type in SUPPORTED_QUEUE_TYPES.items():
        print(f'--> Type {queue_type_name}')
        pcf = None
        try:
            pcf = pymqi.PCFExecute(
                queue_manager, response_wait_interval=timeout, convert=CONFIG['convert_endianness']
            )
            response = pcf.MQCMD_INQUIRE_Q({pymqi.CMQC.MQCA_Q_NAME: b'*', pymqi.CMQC.MQIA_Q_TYPE: queue_type})
        except Exception as e:
            print(f'Error getting queues: {e}')
        else:
            print(f'Number of queues: {len(response)}')

            for queue_info in response:
                queue_name = queue_info[pymqi.CMQC.MQCA_Q_NAME].strip().decode('utf-8')
                pcfq = None
                try:
                    pcfq = pymqi.PCFExecute(
                        queue_manager, response_wait_interval=timeout, convert=CONFIG['convert_endianness']
                    )
                    response = pcfq.MQCMD_INQUIRE_Q({pymqi.CMQC.MQCA_Q_NAME: queue_name.encode('utf-8'), pymqi.CMQC.MQIA_Q_TYPE: pymqi.CMQC.MQQT_ALL})
                except Exception as e:
                    print(f'{queue_name} | statistics: {e}')
                else:
                    print(f'{queue_name} | statistics: success')
                finally:
                    if pcfq is not None:
                        pcfq.disconnect()
        finally:
            if pcf is not None:
                pcf.disconnect()


def get_queue_manager():
    print('Connecting...')
    channel_definition = pymqi.CD()
    channel_definition.ChannelName = CONFIG['channel'].encode('utf-8')
    channel_definition.ConnectionName = f'{CONFIG["host"]}({CONFIG["port"]})'.encode('utf-8')
    channel_definition.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
    channel_definition.TransportType = pymqi.CMQC.MQXPT_TCP
    channel_definition.Version = getattr(pymqi.CMQC, f'MQCD_VERSION_{CONFIG["mqcd_version"]}')

    connection_options = {'cd': channel_definition}
    if 'username' in CONFIG and 'password' in CONFIG:
        connection_options['user'] = CONFIG['username']
        connection_options['password'] = CONFIG['password']

    queue_manager = pymqi.QueueManager(None)
    queue_manager.connect_with_options(CONFIG['queue_manager'], **connection_options)

    print('Connected')
    return queue_manager


CHANNEL_STATUSES = {
    pymqi.CMQCFC.MQCHS_INACTIVE: 'CRITICAL',
    pymqi.CMQCFC.MQCHS_BINDING: 'WARNING',
    pymqi.CMQCFC.MQCHS_STARTING: 'WARNING',
    pymqi.CMQCFC.MQCHS_RUNNING: 'OK',
    pymqi.CMQCFC.MQCHS_STOPPING: 'CRITICAL',
    pymqi.CMQCFC.MQCHS_RETRYING: 'WARNING',
    pymqi.CMQCFC.MQCHS_STOPPED: 'CRITICAL',
    pymqi.CMQCFC.MQCHS_REQUESTING: 'WARNING',
    pymqi.CMQCFC.MQCHS_PAUSED: 'WARNING',
    pymqi.CMQCFC.MQCHS_INITIALIZING: 'WARNING',
}
SUPPORTED_QUEUE_TYPES = {'local': pymqi.CMQC.MQQT_LOCAL, 'model': pymqi.CMQC.MQQT_MODEL}


if __name__ == '__main__':
    main()
