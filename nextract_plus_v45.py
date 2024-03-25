#!/usr/bin/python3
version=45 # March 2024

import hmc_pcm as hmc
import time
import sys
import json

measures = 0
debug = 0

log = 0 # save the line protocal stats to a file called lp.log

if log:
    logfile = open("output_log.json", 'w')

def hint():
    print('Usage:  %s version %d'%(sys.argv[0],version))
    print('%s filename.json - use the JSON file to find the parameters'%(sys.argv[0]))
    print('Example config.json')
    print('{')
    print('"hmc_hostname": "hmc15",')
    print('"hmc_user": "pcmadmin",')
    print('"hmc_password": "panda123sausages!",')
    print('"output_nchart": 0,')
    print('"output_json": 0,')
    print('"output_csv": 0,')
    print('"comment1": "Valid setting for output_influx = 0 (off), 1 or 2",')
    print('"output_influx": 1,')
    print('"comment2": "InfluxDB 1.x options",')
    print('"ihost": "myinflux",')
    print('"iport": "8086",')
    print('"idbname": "nextractplus",')
    print('"iuser": "fred",')
    print('"ipassword": "blogs",')
    print('"comment3": "InfluxDB 2.x options",')
    print('"iurl": "https://influx.acme.com:8086",')
    print('"ibucket": "default",')
    print('"iorg": "IBM",')
    print('"itoken": "123456780..abcdefg_etc.",')
    print('"comment4": "other parameters are ignored",')
    print('"comment5": "last name=value line has no ending comma"')
    print('}')
    sys.exit(0)

if len(sys.argv) == 1:
    hint()

if len(sys.argv) != 2:
    hint()

hmc_hostname="not-found"
hmc_user    ="not-found"
hmc_password="not-found"

try:
    print("%s opening config file:%s"%(sys.argv[0], sys.argv[1]))
    with open(sys.argv[1]) as auth_file:
        auth = json.load(auth_file)
    hmc_hostname=auth["hmc_hostname"]
    hmc_user    =auth["hmc_user"]
    hmc_password=auth["hmc_password"]
except:
    print("Problem loading JSON file %s"%(sys.argv[1]))
    print("hmc_hostname=%s hmc_user=%s hmc_password=%s"%(hmc_hostname,hmc_user,hmc_password))
    sys.exit(0)

if debug:
    print("hmc:" + hmc_hostname + " user:" + hmc_user+ " pass:" + hmc_password)
output_nchart=0
output_json=0
output_csv=0
output_influx=0

try:
    output_nchart=auth["output_nchart"]
    output_json=auth["output_json"]
    output_csv=auth["output_csv"]
    output_influx=auth["output_influx"]
except:
    print("Problem loading JSON file %s"%(sys.argv[1]))
    print("nchart=%d json=%d csv=%d influx-version=%d"
            %(output_nchart, output_json, output_csv, output_influx))
    sys.exit(0)

if output_influx == 1:
    ihost="not-found"
    iport=8086
    idbname="not-found"
    iuser="not-found"
    ipassword="not-found"

    try:
        ihost=auth["ihost"]
        iport=auth["iport"]
        idbname=auth["idbname"]
        iuser=auth["iuser"]
        ipassword=auth["ipassword"]
    except:
        print("Problem loading JSON file %s Influx1"%(sys.argv[1]))
        print("ihost=%s iport=%d idbname=%s iuser=%s ipassword=%s"
                %(ihost, iport, idbname, iuser, ipassword))
        sys.exit(0)

    if debug:
        print("Influx:" + ihost + " Influx port:" + str(iport) + " db:" + idbname)
        print(" user:" + iuser+ " pass:" + ipassword)

    from influxdb import InfluxDBClient
    client = InfluxDBClient(host=ihost, port=iport, username=iuser, password=ipassword, database=idbname)

if output_influx == 2:
    iurl="no-url"
    iorg="no-org"
    itoken="no-token"

    try:
        iurl=auth["iurl"]
        iorg=auth["iorg"]
        itoken=auth["itoken"]
    except:
        print("Problem loading JSON file %s Influx2"%(sys.argv[1]))
        print("iurl=%s iorg=%s itoken=%s"%(iurl, iorg, itoken))
        sys.exit(0)

    if debug:
        print("Influx URL:" + iurl + " Influx Org:" + iorg + " Influx Token:" + itoken)

    from influxdb import InfluxDBClient
    client = InfluxDBClient(url=iurl, token=itoken, org=iorg)
    write_api = client.write_api()


def extract_data(data):
    "fix json by removing arrays of only one item "
    fields = {}
    for key,value in data.items():
        if key == "bridgedAdapters":
            continue
        if key == "transmittedBytes":
            continue
        if key == "physicalLocation": 
            #force to be a string (fix the rare HMC mistake mixed int or string)
            # if not isinstance(value,str);
            #    value=str(value)
            # print("PL FIXED" + str(isinstance(value,str) ))
            value=str(value)
        try:
            fields[key] = float(value[0])
        except:
            fields[key] = value
    return fields

# Create entry[] here to handle the weird case where the HMC returns zero data
# even when it claims data is being collected for the first LPAR 
entry=[]

print("-> nextract_plus version %d saving JSON=%d Influx=%d" % (version, output_json, output_influx))
print("-> Logging on to %s as hmc_user%s" % (hmc_hostname,hmc_user))
hmc = hmc.HMC(hmc_hostname, hmc_user, hmc_password)

print("-> Get Preferences") # returns XML text
prefstripped = hmc.get_stripped_preferences_pcm()
if debug:
    hmc.save_to_file("server_perferences.xml",prefstripped)

print("-> Parse Preferences")
serverlist = hmc.parse_prefs_pcm(prefstripped)  # returns a list of dictionaries one per Server
perflist = []
all_true = True
print("-> ALL servers:")
for num,server in enumerate(serverlist):
    if server['lterm'] == 'true' and server['agg'] == 'true':
        todo = "- OK"
        perflist.append(server)
    else:
        todo = "- remove"
    print('-> Server name=%-16s agg=%-5s longterm=%-5s %s ' 
        %(server['name'], server['agg'], server['lterm'], todo))

print("-> Servers with Perf Stats")
for count, server in enumerate(perflist,start=1):  # just loop the servers with stats
    print('')

#   if server['name'] == 'server_with_no_VIOS':
#      print("Skipping server %s as it has no VIOS" % (server['name']))
#      continue

    print('--> Server=%d Name=%s - Requesting the data ...' %(count,server['name']))
    starttime = time.time()
    filelist = hmc.get_filenames_server(server['atomid'],server['name']) # returns XML of filename(s)
    endtime = time.time()
    print("---> Received %d file(s) in %.2f seconds" % (len(filelist), endtime - starttime))

    if debug:
        for num,file in enumerate(filelist,start=1): # loop around the files
            filename=file['filename']
            print('---> Server=%s File=%d %s' %(server['name'], num,filename))

    if debug:
        hmc.set_debug(True)	 # Warning this generated large files in the debug sub directory

    for num,file in enumerate(filelist,start=1): # loop around the files
        filename=file['filename']
        data = hmc.get_stats(file['url'],filename, server['name']) # returns JSON stats

        if filename[:13] == "ManagedSystem": # start of the filename tells you if server or LPAR
            filename2 = filename.replace('.json','.JSON')
            if debug:
                print('ManagedSystem Saving to file:%s'%(filename2))
                hmc.save_json_txt_to_file(filename2,data)
# ____                           
#/ ___|  ___ _ ____   _____ _ __ 
#\___ \ / _ \ '__\ \ / / _ \ '__|
# ___) |  __/ |   \ V /  __/ |   
#|____/ \___|_|    \_/ \___|_|   

            jdata = json.loads(data)
            info = jdata["systemUtil"]["utilInfo"]
            servername = info['name']

            print("----> Server Name=%s MTM + Serial Number=%s" %( servername, info['mtms'] ))
            print("----> Server Date=%s start=%s end=%s" %(info['startTimeStamp'][:10], info['startTimeStamp'][11:19], info['endTimeStamp'][11:19]))
            print("----> Server DataType=%s Interval=%s seconds" %( info['metricType'],info['frequency'] ))
            if debug:
                print("Info dictionary:")
                print(info)

            utilSamplesArray = jdata['systemUtil']['utilSamples']

            # Create InfluxDB measurements and pump them in
            if debug:
                print("Server stats: %s"%(servername))

            # entry=[] now created above

            for sample in utilSamplesArray:
                timestamp = sample['sampleInfo']['timeStamp']

                try:
                  fields = extract_data(sample['systemFirmwareUtil'])
                  fields['mtm'] = info['mtms']
                  fields['name'] = servername
                  fields['APIversion'] = info['version']
                  fields['metric'] = info['metricType']
                  fields['frequency'] = info['frequency']
                  fields['nextract'] = str(version)

                  data = { 'measurement': 'server_details', 'time': timestamp,
                      'tags': { 'servername': servername },
                      'fields':fields }
                  entry.append(data)
                  if debug: print("has system_details")
                except:
                  if debug: print("no system_details")

                try:
                  data = { 'measurement': 'server_processor', 'time':timestamp,
                      'tags': { 'servername': servername },
                      'fields': extract_data(sample['serverUtil']['processor']) }
                  entry.append(data)
                  if debug: print("has server_processor")
                except:
                  if debug: print("no server_processor")

                try:
                  data = { 'measurement': 'server_memory', 'time': timestamp,
                      'tags': { 'servername': servername },
                      'fields': extract_data(sample['serverUtil']['memory']) }
                  entry.append(data)
                  if debug: print("has server_mem")
                except:
                  if debug: print("no server_mem")

                try:
                  data = { 'measurement': 'server_physicalProcessorPool', 'time': timestamp,
                      'tags': { 'servername': servername },
                      'fields': extract_data(sample['serverUtil']['physicalProcessorPool']) }
                  entry.append(data)
                  if debug: print("has server_physicalProcessorPool")
                except:
                  if debug: print("no server_physicalProcessorPool")

                try:
                  arr = sample['serverUtil']['sharedMemoryPool']
                  for pool in arr:
                      data = { 'measurement': 'server_sharedMemoryPool', 'time': timestamp,
                          'tags': { 'servername': servername, 'pool':pool['id'] },
                          'fields': extract_data(pool) }
                      entry.append(data)
                  if debug: print("has server_sharedMemoryPool")
                except:
                  if debug: print("no server_sharedMemoryPool")

                try:
                  for pool in sample['serverUtil']['sharedProcessorPool']:
                      data = { 'measurement': 'server_sharedProcessorPool', 'time': timestamp,
                          'tags': { 'servername': servername, 'pool':pool['id'], 'poolname':pool['name'] },
                          'fields': extract_data(pool) }
                      entry.append(data)
                  if debug: print("has server_sharedProcessorPool")
                except:
                  if debug: print("no server_sharedProcessorPool")

                try:
                  for adapter in sample['serverUtil']['network']['sriovAdapters']:
                      for adaptport in adapter['physicalPorts']:
                          data = { 'measurement': 'server_sriov', 'time': timestamp,
                              'tags': { 'servername': servername, 
                                        'port': adaptport['id'], 
                                        'location': adaptport['physicalLocation'] },
                              'fields': extract_data(adaptport) }
                          entry.append(data)
                  if debug: print("has server_sriov")
                except:
                  if debug: print("no server_sriov")

                try:
                  for HEA in sample['serverUtil']['network']['HEAdapters']['physicalPorts']:
                      for HEAport in HEA:
                          data = { 'measurement': 'server_HEAport', 'time': timestamp, 
                              'tags': { 'servername': servername, 
                                         'port': HEAport['id'], 
                                         'location': HEAport['physicalLocation'] }, 
                              'fields': extract_data(HEAport) }
                          entry.append(data)
                  if debug: print("has server_net_HEAport")
                except:
                  if debug: print("no server_net_HEAport")

                #__   _(_) ___  ___ 
                #\ \ / / |/ _ \/ __|
                # \ V /| | (_) \__ \
                #  \_/ |_|\___/|___/
                try:
                  vios_array = sample['viosUtil']

                  try:
                    for vios in vios_array:
                       data = { 'measurement': 'vios_details', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name']}, 
                            'fields':{'viosid': vios['id'],'viosname': vios['name'],
                                    'viosstate': vios['state'], 'affinityScore': vios['affinityScore']} }
                       entry.append(data)
                    if debug: print("has VIOS_details")
                  except:
                    if debug: print("no VIOS_details")
  
                  try:
                    for vios in vios_array:
                       data = { 'measurement': 'vios_memory', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name']}, 
                            'fields': extract_data(vios['memory']) }
                       entry.append(data)
                    if debug: print("has VIOS_memory")
                  except:
                    if debug: print("no VIOS_memory")

                  try:
                    for vios in vios_array:
                       data = { 'measurement': 'vios_processor', 
                            'time': sample['sampleInfo']['timeStamp'],
                            'tags': { 'servername': servername, 'viosname': vios['name']}, 
                            'fields': extract_data(vios['processor']) }
                       entry.append(data)
                    if debug: print("has VIOS_processor")
                  except:
                    if debug: print("no VIOS_processor")
  
                  # Networks
                  try:
                    for vios in vios_array:
                       length = len(vios['network']['clientLpars']) 
                       data = { 'measurement': 'vios_network_lpars', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'] },
                            'fields':{ 'clientlpars': length } }
                       entry.append(data)
                    if debug: print("has VIOS_network_lpars")
                  except:
                    if debug: print("no VIOS_network_lpars")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['network']['genericAdapters']:
                         data = { 'measurement': 'vios_network_generic', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'], 
                                      'id': adapt['id'], 'location': adapt['physicalLocation']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_network_generic")
                  except:
                    if debug: print("no VIOS vios_network_generic")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['network']['sharedAdapters']:
                         data = { 'measurement': 'vios_network_shared', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'], 
                                      'id': adapt['id'], 'location': adapt['physicalLocation']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_network_shared")
                  except:
                    if debug: print("no VIOS vios_network_shared")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['network']['virtualEthernetAdapters']:
                         data = { 'measurement': 'vios_network_virtual', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'], 
                                      'location': adapt['physicalLocation'], 
                                      'vswitchid': adapt['vswitchId'], 
                                      'vlanid': adapt['vlanId'] }, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_network_virtual")
                  except:
                    if debug: print("no VIOS vios_network_virtual")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['network']['sriovLogicalPorts']:
                         data = { 'measurement': 'vios_network_sriov', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'],
                                      'location': adapt['physicalLocation'], 
                                      'physicalPortId': adapt['physicalPortId'] }, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_network_sriov")
                  except:
                    if debug: print("no VIOS vios_network_sriov")
  
                  # Storage
                  try:
                    for vios in vios_array:
                       length = len(vios['storage']['clientLpars']) 
                       data = { 'measurement': 'vios_storage_lpars', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'] },
                            'fields':{ 'clientlpars': length } }
                       entry.append(data)
                    if debug: print("has VIOS_storage_lpars") 
                  except:
                    if debug: print("no VIOS_storage_lpars") 
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['storage']['genericVirtualAdapters']:
                         data = { 'measurement': 'vios_storage_virtual', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'],
                                      'id': adapt['id'], 'location': adapt['physicalLocation']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_storage_virtual")
                  except:
                    if debug: print("no VIOS vios_storage_virtual")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['storage']['genericPhysicalAdapters']:
                         data = { 'measurement': 'vios_storage_physical', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'], 
                                      'id': adapt['id'], 'location': adapt['physicalLocation']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_storage_physical")
                  except:
                    if debug: print("no VIOS vios_storage_physical")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['storage']['fiberChannelAdapters']:
                         data = { 'measurement': 'vios_storage_FC', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'], 
                                      'id': adapt['id'], 'location': adapt['physicalLocation']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_storage_FC")
                  except:
                    if debug: print("no VIOS vios_storage_FC")
  
                  try:
                    for vios in vios_array:
                       for adapt in vios['storage']['sharedStoragePools']:
                         data = { 'measurement': 'vios_storage_SSP', 'time': timestamp,
                            'tags': { 'servername': servername, 'viosname': vios['name'],
                                      'id': adapt['id']}, 
                            'fields': extract_data(adapt) }
                         entry.append(data)
                    if debug: print("has VIOS vios_storage_SSP")
                  except:
                    if debug: print("no VIOS vios_storage_SSP")
                except:
                  if debug: print("no VIOS at all")

  
        # _     ____   _    ____  
        #| |   |  _ \ / \  |  _ \ 
        #| |   | |_) / _ \ | |_) |
        #| |___|  __/ ___ \|  _ < 
        #|_____|_| /_/   \_\_| \_\

        if filename[:16] == "LogicalPartition":
            if debug: 
                filename2 = filename + ".xml"
                print('----> Server=%s Filenames XML File=%d bytes=%d name=%s' 
                                %(server['name'],num,len(data),filename2))
                hmc.save_to_file(filename2,data)
                print('----> LPAR on Server=%s Filenames XML File=%d bytes=%d' %(server['name'],num,len(data)))

            filename3, url = hmc.get_filename_from_xml(data)
            # some old HMC versions return duff filenames
            if filename3 == "":
                 continue
            if url == "":
                 continue
            LPARstats = hmc.get_stats(url, filename3, "LPARstats")
            if debug:
                filename3 = filename3.replace('.json','.JSON')
                print('---> Save readable JSON File=%d bytes=%d name=%s' %(num,len(LPARstats),filename3))
                hmc.save_json_txt_to_file(filename3,LPARstats)

            jdata = json.loads(LPARstats)
            servername= jdata["systemUtil"]["utilInfo"]['name'] # name of server
            lparname  = jdata["systemUtil"]["utilSamples"][0]['lparsUtil'][0]['name']
            print('----> LPAR=%s' %(lparname))
            errorlist = {'error'}

            for sample in jdata['systemUtil']['utilSamples']:
                errors = 0
                samplestatus = sample['sampleInfo']['status']
                sampletime   = sample['sampleInfo']['timeStamp']
                if samplestatus != 0 :
                    errmsg = "None"
                    errId = "None"
                    uuid = "None"
                    reportedBy = "None"
 
                    try:
                        errmsg     = sample['sampleInfo']['errorInfo'][0]['errMsg']
                        errId      = sample['sampleInfo']['errorInfo'][0]['errId']
                        uuid       = sample['sampleInfo']['errorInfo'][0]['uuid']
                        reportedBy = sample['sampleInfo']['errorInfo'][0]['reportedBy']
                    except:
                        print("Error State non-zero but there is no error messages . . . continuing")
                    
                    errors+= 1
                    e_before=len(errorlist)
                    error = "%s%d%s%s%s" %(servername,samplestatus,errId, reportedBy,errmsg)
                    errorlist.add(error)
                    e_after=len(errorlist)
                    if e_before != e_after:  # ie the error was added so its new so print it
                        print("ERROR Server=%s LPAR=%s: Status=%d errId=%s From=%s\nERROR Description=%s\n" 
                                 %(servername,lparname,samplestatus,errId, reportedBy,errmsg))

                for lpar in sample['lparsUtil']:
                    
                    try:
                      data = { 'measurement': 'lpar_details', 'time': sampletime,
                          'tags': { 'servername': servername, 'lparname': lparname },
                          'fields': {
                                "id": lpar['id'],
                                "name": lpar['name'],
                                "state": lpar['state'],
                                "type": lpar['type'],
                                "osType": lpar['osType'],
                                "affinityScore": lpar['affinityScore'] } }
                      entry.append(data)
                      if debug: print("has lpar_details %s %s %s"%(servername,lparname,sampletime))
                    except:
                      if debug: print("no lpar_details %s %s %s"%(servername,lparname,sampletime))

                    try:
                      data = { 'measurement': 'lpar_processor', 'time': sampletime,
                          'tags': { 'servername': servername, 'lparname': lparname },
                          'fields': extract_data(lpar['processor']) }
                      entry.append(data)
                      if debug: print("has lpar_processor %s %s %s"%(servername,lparname,sampletime))
                    except:
                      if debug: print("no lpar_processor %s %s %s"%(servername,lparname,sampletime))

                    try:
                      data = { 'measurement': 'lpar_memory', 'time': sampletime,
                          'tags': { 'servername': servername, 'lparname': lparname },
                          'fields': extract_data(lpar['memory']) }
                      entry.append(data)
                      if debug: print("has lpar_memory %s %s %s"%(servername,lparname,sampletime))
                    except:
                      if debug: print("no lpar_memory %s %s %s"%(servername,lparname,sampletime))

                    if debug: print("LPAR state = |%s| %s %s %s"%(lpar['state'],servername,lparname,sampletime))
                    if lpar['state'] == "Not Activated":
                      continue  # Skip the below as they are only available for state=Active LPARs

                    # Networks
                    try:
                        for net in lpar['network']['virtualEthernetAdapters']:
                            try:
                                data = { 'measurement': 'lpar_net_virtual', 'time': sampletime,
                                    'tags': { 'servername': servername, 'lparname': lparname,
                                              'location': net['physicalLocation'],
                                              'vlanId': net['vlanId'], 
                                              'vswitchId': net['vswitchId'] },
                                    'fields': extract_data(net) }
                                entry.append(data)
                                if debug: print("has lpar_net_virtual")
                            except:
                                if debug: print("no lpar_net_virtual")
                        if debug: print("has lpar_net_virtual %s %s %s"%(servername,lparname,sampletime))
                    except:
                        if debug: print("no lpar_net_virtual %s %s %s"%(servername,lparname,sampletime))

                    try:
                        for net in lpar['network']['sriovLogicalPorts']:
                            if debug: print(net)
                            try:
                                data = { 'measurement': 'lpar_network_sriov', 'time': sampletime,
                                    'tags': { 'servername': servername, 'lparname': lparname,
                                              'location': net['physicalLocation'],
                                              'physicalPortId': net['physicalPortId'] },
                                    'fields': extract_data(net) }
                                entry.append(data)
                                if debug: print(data)
                            except:
                                if debug: print("no lpar_network_sriov")
                        if debug: print("has lpar_network_sriov %s %s %s"%(servername,lparname,sampletime))
                    except:
                        if debug: print("no lpar_network_sriov %s %s %s"%(servername,lparname,sampletime))

                    # Storage
                    try:
                        for store in lpar['storage']['genericVirtualAdapters']:
                            try:
                                data = { 'measurement': 'lpar_storage_virtual', 'time': sampletime,
                                    'tags': { 'servername': servername, 'lparname': lparname,
                                              'id': store['id'], 
                                              'location': net['physicalLocation'],
                                              'viosId': store['viosId'] },
                                    'fields': extract_data(store) }
                                entry.append(data)
                            except:
                                if debug: print("no lpar_storage_virtual")
                        if debug: print("has lpar_storage_virtual %s %s %s"%(servername,lparname,sampletime))
                    except:
                        if debug: print("no lpar_storage_virtual %s %s %s"%(servername,lparname,sampletime))

                    try:
                        for store in lpar['storage']['virtualFiberChannelAdapters']:
                            try:
                                data = { 'measurement': 'lpar_storage_vFC', 'time': sampletime,
                                    'tags': { 'servername': servername, 'lparname': lparname,
                                              'location': store['physicalLocation'], 
                                              'viosId': store['viosId'] },
                                    'fields': extract_data(store) }
                                entry.append(data)
                            except:
                                if debug: print("no lpar_storage_vFC")
                        if debug: print("has lpar_storage_vFC %s %s %s"%(servername,lparname,sampletime))
                    except:
                        if debug: print("no lpar_storage_vFC %s %s %s"%(servername,lparname,sampletime))




        # PUSH TO INFLUXDB FOR EACH FILE if more than 25000 lines of data ready
        if len(entry) > 25000:
            print("Adding %d records to InfluxDB for Server=%s"%(len(entry),servername))
            measures = measures + len(entry)

            if log:
                for line in entry:
                    logfile.write(str(line))
                    logfile.write("\n")

            if output_influx == 1:
                client.write_points(entry)

            if output_influx == 2:
                write_api.write(ibucket, iorg, entry)

            if output_json == 1:
                for item in entry:
                    JSONfile.write(str(item) + "\n")
            entry=[] # empty the list

    # PUSH TO INFLUXDB FOR EACH SERVER
    if len(entry) > 0:

        if log:
            for line in entry:
                logfile.write(str(line))
                logfile.write("\n")

        if output_influx ==1 or output_influx == 2:
            client.write_points(entry)
        print("Added %d records to InfluxDB for Server=%s"%(len(entry),servername))
        measures = measures + len(entry)
        if output_json == 1:
            for item in entry:
                JSONfile.write(str(item) + "\n")

if output_json == 1:
    JSONfile.close()
if log:
    logfile.close()

print("Logging off the HMC - found %d measures"%(measures))
hmc.logoff()