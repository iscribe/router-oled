
import os
import sys
import time
import pickle
import calendar
import requests
import xmltodict
import speedtest

import logging as log

from lte_constants import SIGNAL_PERCENT, STATUS, NETWORK, SIGNAL_ICON_1, SIGNAL_ICON_2

SIGNAL_ICON = SIGNAL_ICON_1


def get_token(device_ip):
    token = None
    sessionID = None
    try:
        r = requests.get(url='http://' + device_ip + '/api/webserver/SesTokInfo', allow_redirects=False, timeout=(2.0,2.0))
    except requests.exceptions.RequestException as e:
        log.error("Unable to get token/sessionID: {}".format(e))
        return (token, sessionID)
        
    try:        
        d = xmltodict.parse(r.text, xml_attribs=True)
        if 'response' in d and 'TokInfo' in d['response']:
            token = d['response']['TokInfo']
        if 'response' in d and 'SesInfo' in d['response']:
            sessionID = d['response']['SesInfo']
    except:
        pass
    return (token, sessionID)

def call_api(device_ip, token, sessionID, resource, xml_attribs=True):
    headers = {}
    if token is not None and sessionID is not None:
        headers = {'__RequestVerificationToken': token}
        headers = {'Cookie': sessionID}
    try:
        r = requests.get(url='http://' + device_ip + resource, headers=headers, allow_redirects=False, timeout=(2.0,2.0))
    except requests.exceptions.RequestException as e:
        print ("Error: "+str(e))
        return False;

    if r.status_code == 200:
        d = xmltodict.parse(r.text, xml_attribs=xml_attribs)
        if 'error' in d:
            raise Exception('Received error code ' + d['error']['code'] + ' for URL ' + r.url)
        return d            
    else:
      raise Exception('Received status code ' + str(r.status_code) + ' for URL ' + r.url)

def _iter_items(device_ip, token, sessionID, resource, items):
    d = call_api(device_ip, token, sessionID, resource)
    data={}
    log.debug("{}: {}".format(resource, d))
    for item in items:
        if item in d['response'] and d['response'][item]:
            data[item] = d['response'][item]
        else:
            log.warn("Missing item: {}".format(item))
        
    return data

def device_info(device_ip, token, sessionID):
    items = [
        'DeviceName', 'SerialNumber', 'Imei', 'HardwareVersion', 
        'SoftwareVersion', 'WebUIVersion', 'MacAddress1',
        'MacAddress2', 'ProductFamily', 'WanIPAddress'
    ]
    resource = '/api/device/information'
        
    return _iter_items(device_ip, token, sessionID, resource, items)

def _getExternalIP(cacheTimeout=3600, ipCacheFile="/tmp/ipCacheFile"):
    ip = None
    if os.path.isfile(ipCacheFile):
        fileage = int(calendar.timegm(time.gmtime())) - int(os.stat(ipCacheFile).st_ctime)
        log.debug("IP cache file age: {} second(s)".format(fileage))
        
        if fileage < cacheTimeout:
            log.debug("Reading external ip from cache")
            log.warn("not implemented")
        else:
            try:
                r = requests.get('http://ip.o11.net', timeout=(2.0,2.0))
            except Exception as e:
                log.error("Failed to contact ip server")
                
            if r.status_code == 200:
                ip = r.text.rstrip()
                try:
                    with open(ipCacheFile, "w") as f:
                        f.write(ip)
                except Exception as  e:
                    log.error("Unable to write ipCacheFile: {}".format(e))
                
                return
    else:
        log.debug("No IP cache file exists")
        try:
            r = requests.get('http://ip.o11.net', timeout=(2.0,2.0))
            if r.status_code == 200:
                ip = r.text.rstrip()
                with open(ipCacheFile, "w") as f:
                    f.write(ip)
        except Exception as  e:
            log.error("Unable to write ipCacheFile: {}".format(e))
            return
        
   


    with open(ipCacheFile) as f:
        return f.read()



def connection_info(device_ip, token, sessionID):
    items = [
        'ConnectionStatus', 'SignalIcon',
        'CurrentNetworkType', 'RoamingStatus'
        'PrimaryDns', 'SecondaryDns'
    ]
    resource = '/api/monitoring/status'
    
    data = _iter_items(device_ip, token, sessionID, resource, items)
    if 'SignalIcon' in data:
        data['SignalPercentage'] = SIGNAL_PERCENT[data['SignalIcon']]
        data['SignalStrength'] = data['SignalIcon']
        data['SignalIcon'] = SIGNAL_ICON[data['SignalIcon']]
    
    if 'ConnectionStatus' in data:
        data['ConnectionStatus'] = STATUS[data['ConnectionStatus']]
        if data['ConnectionStatus'] == "Connected":
            data['ExternalIPAddress'] = _getExternalIP()
    
    if 'CurrentNetworkType' in data:
        data['CurrentNetworkType'] = NETWORK[data['CurrentNetworkType']]
    
    return data
    
def provider_info(device_ip, token, sessionID):
    items = ['State', 'FullName']
    resource = '/api/net/current-plmn'
    
    data = _iter_items(device_ip, token, sessionID, resource, items) 
    return data
    
def traffic_info(device_ip, token, sessionID):
    items = ['CurrentConnectTime', 'CurrentUpload', 'CurrentDownload', 'TotalUpload', 'TotalDownload']
    resource = '/api/monitoring/traffic-statistics'

    data = _iter_items(device_ip, token, sessionID, resource, items)
    return data
    
def sms_info(device_ip, token, sessionID):
    items = ['UnreadMessage']
    resource = '/api/monitoring/check-notifications'
    
    data = _iter_items(device_ip, token, sessionID, resource, items)
    return data

def speed_info():

        cacheTimeout = 3600
        cacheFile = "/tmp/speedTestCache.txt"
        result_string = None

        data = {}

        if os.path.isfile(cacheFile):
            fileage = int(calendar.timegm(time.gmtime())) - int(os.stat(cacheFile).st_ctime)
        else:
            fileage = 9999999999

        if fileage > cacheTimeout:
            s = speedtest.Speedtest()
            s.get_servers([])
            s.get_best_server()
            s.download(threads=None)
            s.upload(threads=None)
            result = s.results.dict()
            print(result)

            data['DownloadSpeed'] = round((result['download'] / 1000 / 1000), 1)
            data['UploadSpeed'] = round((result['upload'] / 1000 /1000), 1)
            data['Ping'] = result['ping']

            result_string = "{}d {}u".format(round((result['download'] / 1000 / 1000), 1), round((result['upload'] / 1000 / 1000), 1), result['ping'])
            
            try:
                with open(cacheFile, "wb") as f:
                    #f.write(result_string)
                    pickle.dump(data, f)
            except Exception as e:
                print("Failed to pickle speed test: {}".format(e))
        else:
            print("fileage is {}/{}, loading from cache".format(fileage, cacheTimeout))
            with open(cacheFile) as f:
                # result_string = f.read()
                data = pickle.load(f)
        
        return data
    
def get_dongle_info(devIP="192.168.8.1", loglevel=log.INFO):
    log.basicConfig(level=loglevel)
    token, sessionID = get_token(devIP)
    if token is None or sessionID is None:
        raise ConnectionError("Unable to communicate with the dongle")

    log.debug("\tToken:     {}".format(token))
    log.debug("\tSessionID: {}".format(sessionID))
    
    data = device_info(devIP, token, sessionID)
    data.update(connection_info(devIP, token, sessionID))
    data.update(provider_info(devIP, token, sessionID))
    data.update(traffic_info(devIP, token, sessionID))
    data.update(sms_info(devIP, token, sessionID))
    data.update(speed_info())
    
    return data


def main():
    # log.basicConfig(level=log.INFO)
    
    print("LTE Modem Stats")
    
    data = get_dongle_info()
    for i in data:
        log.info("{}:{}".format(i, data[i]))
        



if __name__ == "__main__":
    sys.exit(main())




