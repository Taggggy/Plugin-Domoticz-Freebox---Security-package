#Code adapté de http://www.manatlan.com/blog/freeboxv6_api_v3_avec_python

import urllib.request,hmac,json,hashlib,time,Domoticz, datetime
from urllib.request import urlopen,Request
from socket import timeout
import pandas as pd

class FbxCnx:
    def __init__(self,host="mafreebox.free.fr"):
        self.host=host

    def register(self,appid,appname,version,devname):
        data={'app_id': appid,'app_name': appname,'app_version':version,'device_name': devname}
        result=self._com("login/authorize/",data)
        if not result["success"]:
            return "Erreur Reponse Freebox : " + result["msg"]
        r=result["result"]
        trackid,token=r["track_id"],r["app_token"]
        s="pending"
        nbWait = 0
        while s=="pending":
            s=self._com("login/authorize/%s"%trackid)
            s = s["result"]["status"]
            time.sleep(1)
            nbWait = nbWait + 1
            if nbWait > 30:
                s = "TropLong"
        return s=="granted" and token

    def _com(self,method,data=None,headers=None):
        url = self.host+"/api/v7/"+method
        if data: 
            data = json.dumps(data) #On transforme en string le dict
            data = data.encode() #On transforme en tableau de byte le string pour Request
            request = Request(url, data=data)
            request.get_method = lambda:"POST"
        else:
            if headers:
                request = Request(url,headers=headers)
            else:
                request = Request(url)
        res = urlopen(request,timeout=2).read()
        return json.loads(res.decode())

    def _put(self,method,data=None,headers=None):
        url = self.host+"/api/v7/"+method
        if data: 
            data = json.dumps(data) #On transforme en string le dict
            data = data.encode() #On transforme en tableau de byte le string pour Request
            if headers:
                request = Request(url,data=data,headers=headers)
            else:
                request = Request(url, data=data)
            request.get_method = lambda:"PUT"
        else:
            if headers:
                request = Request(url,headers=headers)
            else:
                request = Request(url)
        res = urlopen(request,timeout=2).read()
        return json.loads(res.decode())

    def _get(self,method,data=None,headers=None):
        url = self.host+"/api/v7/"+method
        if headers:
            request = Request(url,headers=headers)
        else:
            request = Request(url)
        request.get_method = lambda:"GET"
        res = urlopen(request,timeout=2).read()
        return json.loads(res.decode())

    def _mksession(self):
        challenge=self._com("login/")["result"]["challenge"]
        data={
          "app_id": self.appid,
          "password": hmac.new(self.token.encode(),challenge.encode(),hashlib.sha1).hexdigest()
        }
        return self._com("login/session/",data)["result"]["session_token"]

class FbxApp(FbxCnx):
    def __init__(self,appid,token,session=None,host="mafreebox.free.fr"):
        FbxCnx.__init__(self,host)
        self.appid,self.token=appid,token
        self.session=session if session else self._mksession()

    def com(self,method,data=None):
        return self._com(method,data,{"X-Fbx-App-Auth": self.session})

    def put(self,method,data=None):
        return self._put(method,data,{"X-Fbx-App-Auth": self.session})

    def get(self,method,data=None):
        return self._get(method,data,{"X-Fbx-App-Auth": self.session})

    def diskinfoRaw(self):
        listDiskRaw = self.com( "storage/disk/")
        if (listDiskRaw is not None):
            return json.dumps(listDiskRaw)
        else:
            return "null"

    def diskinfo(self):
        retour = {}
        try:
            listDisk = self.com( "storage/disk/")
            if ("result" in listDisk): #Pour la box mini 4K qui n'a pas de disk
                for disk in listDisk["result"]:
                    if ("partitions" in disk): #Pour la box mini 4K qui n'a pas de disk
                        for partition in disk["partitions"]:
                            label = partition["label"]
                            used =partition["used_bytes"]
                            total=partition["total_bytes"]
                            Domoticz.Debug('Disk '+label+' '+str(used)+'/'+str(total))
                            percent = 0
                            if (total is not None):
                                if (total > 0):
                                    percent = used/total*100
                                    # print(str(label)+"=>"+str(round(percent,2))+"%")
                                    retour.update({str(label):str(round(percent,2))})   
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
            return retour
        except timeout:
            Domoticz.Error('Timeout') #on ne fait rien, on retourne une liste vide
            return retour
        return retour
    
    def getNameByMacAdresse(self,p_macAdresse):
        try:
            listePeriph = self.com( "lan/browser/pub/")
            for periph in listePeriph["result"]:
                macAdresse = periph["id"]
                if(("ETHER-"+p_macAdresse.upper()) == macAdresse.upper()):
                    return periph["primary_name"]
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            return ""
    
    def isPresenceByMacAdresse(self,p_macAdresse):
        try:
            listePeriph = self.com( "lan/browser/pub/")
            for periph in listePeriph["result"]:
                macAdresse = periph["id"]
                if(("ETHER-"+p_macAdresse.upper()) == macAdresse.upper()):
                    reachable = periph["reachable"]
                    active = periph["active"]
                    if reachable and active:
                        return True
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout') #on ne fait rien, on retourne faux
        return False

    def lanPeripherique(self):
        retour = {}
        try:
            listePeriph = self.com( "lan/browser/pub/")
            for periph in listePeriph["result"]:
                name = periph["primary_name"]
                reachable = periph["reachable"]
                active = periph["active"]
                macAdresse = periph["id"]
                if reachable and active:
                    retour.update({macAdresse:name})
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout') #on ne fait rien, on retourne une liste vide
        return retour

    def sysinfo(self):
        retour = {}
        try:
            sys = self.com( "system/")
            retour.update({str('temp_cpub'):str(round(sys["result"]["temp_cpub"],2))})
            retour.update({str('temp_sw'):str(round(sys["result"]["temp_sw"],2))})
            retour.update({str('temp_cpum'):str(round(sys["result"]["temp_cpum"],2))})
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout') #on ne fait rien, on retourne une liste vide
        return retour

    def isOnWIFI(self):
        try:
            v_result = self.get("wifi/config/")
            if(v_result["result"]["enabled"]):
                return 1
            else:
                return 0
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            return 0

    def setOnOFFWifi(self, p_isPutOn):
        isOn = None
        if p_isPutOn:
            # data = {'ap_params': {'enabled': True}}
            data = {'enabled': True}          
        else:
            # data = {'ap_params': {'enabled': False}}
            data = {'enabled': False}
        try:
            v_result = self.put( "wifi/config/",data)
            isOn = False
            if True == v_result['success']:
                if v_result['result']['enabled']: #v_result['result']['ap_params']['enabled']:
                    Domoticz.Debug( "Wifi is now ON")
                    isOn = True
                else:
                    Domoticz.Debug("Wifi is now OFF")
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('setOnOFFWifi Erreur '+ error.msg)
        except timeout:
            if not p_isPutOn:
                # If we are connected using wifi, disabling wifi will close connection
                # thus PUT response will never be received: a timeout is expected
                Domoticz.Error("Wifi désactivé")
                return False
            else:
                # Forward timeout exception as should not occur
                raise timeout
        return isOn
    
    def reboot(self):
        v_result = self.com("system/reboot/")
        if not v_result['success']:
            Domoticz.Error("Erreur lors du Reboot")
        else:
            Domoticz.Debug("Freebox Server en cours de reboot.")

    def sensor(self):
        allowedNodesType = ["Détecteur de mouvement infrarouge", "Détecteur d'ouverture de porte"]
        states = {}
        batteries = {}
        try:
            nodes = self.com("home/nodes")
            if not nodes['success']:
                Domoticz.Error("Erreur lors de l'accès à l'état des nodes")
            else:
                for node in nodes['result']:
                    if node['type']['label'] in allowedNodesType :
                        label = node['label']
                        value = not (node['show_endpoints'][6]['value'])
                        states.update({label:value})
                        battery = node['show_endpoints'][8]['value']
                        batteries.update({label:battery})

        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de sensor') #on ne fait rien, on retourne une liste vide
        return (states, batteries)

    def camera(self, link):
        TIME_ON = 60 #Si la dernière vidéo enregistrée date de moins de 1 minute alors on dit que la caméra est activée
        #Lecture des `table` de la page HTML
        try:
            table = pd.read_html(link)[0]
            #Dernière entrée dans la table, colonne des timestamp
            lastVideo = table[1][len(table[1]) - 1]
            #Récupération du timestamp de la dernière vidéo enregistrée
            timestamp = int(lastVideo[:str.find(lastVideo, ".mp4")])
            timestampNow = datetime.datetime.now().timestamp()
            if ((timestampNow - timestamp) < TIME_ON):
                return True
            else:
                return False
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de camera')

    def getID(self, component):
        #"Télécommande pour alarme" ou "Système d'alarme" classiquement
        try:
            nodes = self.com("home/nodes")
            for node in nodes['result']:
                if node['type']['label'] == component:
                    return node['id']
            Domoticz.Debug("Pas trouvé l'id")
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de getID')

    def isAlarmOn(self):
        idAlarm = self.getID("Système d'alarme")
        try:
            v_result = self.com("home/endpoints/"+ str(idAlarm) + "/11")
            if(v_result['result']['value'] == "idle"):
                return False
            else:
                return True
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de isAlarmOn')

    def setAlarmOn(self, p_activate):
        idAlarm = self.getID("Système d'alarme")
        data = {"value":"true","value_type":"bool"}
        if p_activate:
            target = "home/endpoints/" + str(idAlarm) + "/1" #Activer alarme principale
        else:
            target = "home/endpoints/" + str(idAlarm) + "/4" #Desactiver alarme
        try:
            v_result = self.put(target,data)
            isOn = False
            if v_result['success']:
                if v_result['result']['value']:
                    Domoticz.Debug( "FREEBOX Alarm is now ON")
                    isOn = True
                else:
                    Domoticz.Debug("FREEBOX Alarm is now OFF")
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('setAlarm Erreur '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de setAlarmOn')

        return isOn

    def getAlarmBattery(self):
        idAlarm = self.getID("Système d'alarme")
        try:
            v_result = self.com("home/endpoints/"+ str(idAlarm) + "/19") #Batterie de l'alarme principale
            if v_result['success']:
                return v_result['result']['value']
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de getAlarmBattery')

    def getRemoteBattery(self):
        idRemote = self.getID("Télécommande pour alarme")
        try:
            v_result = self.com("home/endpoints/"+ str(idRemote) + "/3") #Batterie de la télécommande
            if v_result['success']:
                return v_result['result']['value']
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de getRemoteBattery')

    def getRemoteInput(self):
        TIME_ON = 60
        idRemote = self.getID("Télécommande pour alarme")
        try:
            v_result = self.com("home/tileset/"+ str(idRemote))
            if v_result['success']:
                history = v_result['result'][0]['data'][1]['history'] #Historique
                lastInput = history[len(history) - 1]
                timestampLastInput = lastInput['timestamp']
                timestampNow = datetime.datetime.now().timestamp()
                if ((timestampNow - timestampLastInput) < TIME_ON):
                    if lastInput['value'] == "1":
                        return 0 #Activation de l'alarme
                    else:
                        return 1 #Désactivation de l'alarme
                else:
                    return -1 #Inchangé

        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            Domoticz.Error('La Freebox semble indisponible : '+ error.msg)
        except timeout:
            Domoticz.Error('Timeout de getRemoteInput')