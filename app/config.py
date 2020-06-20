IP = '192.168.20.213'

URL = {
    'regist_url': 'http://'+IP+':40200/s_config/v1.0/regist_config',
    'unregist_url': 'http://'+IP+':40200/s_config/v1.0/unregist_config',
    'getconfig_url': 'http://'+IP+':40200/s_config/v1.0/get_configs',
    'setconfig_url': 'http://'+IP+':40200/s_config/v1.0/set_configs',
}
client = [
    's_opcda_client1',
    's_opcda_client2',
    's_opcda_client3',
    's_opcae_client1',
    's_opcae_client2',
    's_opcae_client3'
]

server = ['s_opcda_server1',
          's_opcda_server2',
          's_opcda_server3']
opc = [
    's_opcda_server1',
    's_opcda_server2',
    's_opcda_server3',
    's_opcda_client1',
    's_opcda_client2',
    's_opcda_client3',
    's_opcae_client1',
    's_opcae_client2',
    's_opcae_client3'
]

modbus = ['modbus1', 'modbus2']


