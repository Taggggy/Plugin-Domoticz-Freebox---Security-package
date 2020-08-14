# Freebox Python Plugin
#
# Author: https://matdomotique.wordpress.com/
# https://matdomotique.wordpress.com/2018/03/25/plugin-freebox-pour-domoticz/
#
"""
<plugin key="Freebox" name="Freebox Python Plugin" author="supermat, modifié par Tagggy" version="2.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://matdomotique.wordpress.com/2018/03/25/plugin-freebox-pour-domoticz">
    <params>
        <param field="Address" label="URL de la Box avec http devant" width="400px" required="true" default="http://mafreebox.free.fr"/>
        <param field="Port" label="Port" width="100px" required="true" default="80"/>
        <param field="Mode1" label="Token" width="600px"/>
        <param field="Mode2" label="Lien d'accès au disque dur de la Freebox" width="600px" />
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz,freebox,json,os,datetime,time
# from data import * #Pour le debug local sinon à mettre en commentaire
from enum import Enum

class FreeboxPlugin:
    class DeviceType(Enum):
        deviceTypeDisk = 'DiskDevice'
        deviceSystemInfo = 'SystemInfoDevice'
        devicePresence = 'PresenceDevice'
        deviceCommande = 'Commande'
    _fileNameDeviceMapping = 'devicemapping.json'
    enabled = False
    token = ""
    freeboxURL = "http://mafreebox.free.fr"
    _UNIT_DISK = {}
    _lastExecution = datetime.datetime.now()
    def __init__(self):
        #self.var = 123
        return

    def getDicoUnitAllDevice(self):
        v_UnitKeyDico = {}
        if (os.path.isfile(self._fileNameDeviceMapping)):
                with open(self._fileNameDeviceMapping) as data_file:
                    v_UnitKeyDico = json.load(data_file)
        return v_UnitKeyDico

    def saveDicoUnitDevice(self, p_dicoToSave):
        with open(self._fileNameDeviceMapping, 'w', encoding='utf-8') as data_file:
                json.dump(p_dicoToSave, data_file)

    def getNextUnsuedUnit(self,p_dicoAll):
        v_count = 0
        for deviceType in p_dicoAll:
            v_count = v_count + len(p_dicoAll[deviceType])
        return v_count+1

    def getOrCreateUnitIdForDevice(self, p_deviceType, p_deviceFreeboxName):
        # v_UnitKeyDico = self.getDicoUnitForDeviceType(p_deviceType)
        v_dicoAll = self.getDicoUnitAllDevice()
        if(p_deviceType.value in v_dicoAll):
            v_dicoDeviceType = v_dicoAll[p_deviceType.value]
        else:
            v_dicoDeviceType = {}
            v_dicoAll.update({p_deviceType.value:v_dicoDeviceType})
        if(p_deviceFreeboxName in v_dicoDeviceType):
            return v_dicoDeviceType[p_deviceFreeboxName]
        else:
            v_unit = self.getNextUnsuedUnit(v_dicoAll)
            v_dicoDeviceType.update({p_deviceFreeboxName:v_unit})
            self.saveDicoUnitDevice(v_dicoAll)
            return v_unit
    
    def isUnitExist(self, p_deviceType, p_deviceFreeboxName):
        v_dicoAll = self.getDicoUnitAllDevice()
        if(p_deviceType.value in v_dicoAll):
            v_dicoDeviceType = v_dicoAll[p_deviceType.value]
        else:
            return False
        if(p_deviceFreeboxName in v_dicoDeviceType):
            return True
        else:
            return False

    def updateDeviceIfExist(self,  p_deviceType, p_deviceFreeboxName, p_nValue, p_sValue, p_BatteryLevel):
        if self.isUnitExist(p_deviceType,p_deviceFreeboxName):
            v_unitKey = self.getOrCreateUnitIdForDevice(p_deviceType,p_deviceFreeboxName)
            Devices[v_unitKey].Update(nValue=p_nValue, sValue=p_sValue, BatteryLevel=p_BatteryLevel)
            Domoticz.Debug("Le dipositif de type "+p_deviceType.value +" associé à "+ p_deviceFreeboxName + " a été mis à jour " + str(p_nValue) + "/" + str(p_sValue) + ". Batterie: " + str(p_BatteryLevel) + "%")
        #     if v_unitKey in Devices:
        #         # On ne met pas à jour un device de type devicePresence s'il est déjà à jour
        #         if(p_deviceType.value != self.DeviceType.devicePresence.value
        #            or (p_deviceType.value == self.DeviceType.devicePresence.value
        #                 and Devices[v_unitKey].sValue != p_sValue)
        #         ):
        #             Devices[v_unitKey].Update(nValue=p_nValue, sValue=p_sValue, BatteryLevel=p_BatteryLevel)
        #             Domoticz.Debug("Le dipositif de type "+p_deviceType.value +" associé à "+ p_deviceFreeboxName + " a été mis à jour " + str(p_nValue) + "/" + str(p_sValue))
        #         else:
        #             Domoticz.Debug("Le dipositif de type "+p_deviceType.value +" associé à "+ p_deviceFreeboxName + " est déjà à jour.")
        #     else:
        #         Domoticz.Debug("Le dipositif de type "+p_deviceType.value +" associé à "+ p_deviceFreeboxName + " a été supprimé dans Domoticz.")
        # else:
        #     Domoticz.Debug("Le dipositif de type "+p_deviceType.value +" associé à "+ p_deviceFreeboxName + " n'a pas été créé dans Domoticz. Veuillez désactiver et réactiver le plugin, en autorisant l'ajout de nouveaux dispositifs.")

    def onStart(self):
        Domoticz.Debug("onStart called")
        try:
            self.freeboxURL = Parameters["Address"]+":"+Parameters["Port"]
            if Parameters["Mode6"] == "Debug":
                Domoticz.Debugging(1)
            DumpConfigToLog()
            if Parameters["Mode1"] == "": # Le Token
                Domoticz.Log("C'est votre première connexion, le token n'est pas renseigné.")
                Domoticz.Log("Vous avez 30 secondes pour autoriser le plugin sur l'écran de la Freebox.")
                Domoticz.Log("Une fois autorisé sur la Freebox, le token s'affichera ici.")
                Token = freebox.FbxCnx(self.freeboxURL).register("idPluginDomoticz","Plugin Freebox","1","Domoticz")
                if Token:
                    Domoticz.Log("------------------------------------------------------------------------------")
                    Domoticz.Log("Veuillez copier ce token dans la configuration du plugin Reglages > Matériel")
                    Domoticz.Log(Token)
                    Domoticz.Log("------------------------------------------------------------------------------")
                else:
                    Domoticz.Log("Vous avez été trop long (ou avez refusé), veuillez désactiver et réactiver le matériel Reglages > Matériel.")
            else:
                self.token = Parameters["Mode1"]
                Domoticz.Log("Token déjà présent. OK.")

                f=freebox.FbxApp("idPluginDomoticz",self.token,host=self.freeboxURL)

                Domoticz.Heartbeat(5)
                #Creation du device pour le détecteur d'ouverture

                (v_sensors, batteries) = f.sensor()
                for sensor in v_sensors:
	                keyunit = self.getOrCreateUnitIdForDevice(self.DeviceType.devicePresence, sensor)
	                if (keyunit not in Devices):
	                    v_dev = Domoticz.Device(Unit=keyunit, Name=sensor, TypeName="Motion")
	                    v_dev.Create()
	                    Domoticz.Log("Création du dispositif " + sensor)

                keyunit = self.getOrCreateUnitIdForDevice(self.DeviceType.devicePresence, "FREEBOX - Caméra")
                if (keyunit not in Devices):
                	v_dev = Domoticz.Device(Unit=keyunit, Name= "FREEBOX - Caméra", TypeName="Motion")
                	v_dev.Create()
                	Domoticz.Log("Création du dispositif " + "FREEBOX - Caméra")

                keyunit = self.getOrCreateUnitIdForDevice(self.DeviceType.deviceCommande,"FREEBOX - Alarme")
                if (keyunit not in Devices):
                    v_dev = Domoticz.Device(Unit=keyunit, Name="FREEBOX - Alarme", TypeName="Switch")
                    v_dev.Create()
                    Domoticz.Log("Création du dispositif " + "FREEBOX - Alarme")

                keyunit = self.getOrCreateUnitIdForDevice(self.DeviceType.deviceCommande,"FREEBOX - Télécommande")
                if (keyunit not in Devices):
                    v_dev = Domoticz.Device(Unit=keyunit, Name="FREEBOX - Télécommande", TypeName="Switch")
                    v_dev.Create()
                    Domoticz.Log("Création du dispositif " + "FREEBOX - Télécommande")
                
                DumpConfigToLog()
        except Exception as e:
            Domoticz.Log("OnStart error: "+str(e))

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        try:
            Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

            keyunit = self.getOrCreateUnitIdForDevice(self.DeviceType.deviceCommande,"FREEBOX - Alarme")
            if (keyunit == Unit):
                f=freebox.FbxApp("idPluginDomoticz",self.token,host=self.freeboxURL) 
                if(str(Command) == "On"):
                    f.setAlarmOn(True)
                    self.updateDeviceIfExist(self.DeviceType.deviceCommande,"FREEBOX - Alarme",True, "True")
                else:
                    f.setAlarmOn(False)
                    self.updateDeviceIfExist(self.DeviceType.deviceCommande,"FREEBOX - Alarme",False, "False")
        except (KeyError):
            pass

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        try:
            if self.token == "" :
                Domoticz.Log("Pas de token défini.")
                return
            f=freebox.FbxApp("idPluginDomoticz",self.token,host=self.freeboxURL)
            

            (sensorsState, sensorBatteries) = f.sensor()
            for sensor in sensorsState:
                self.updateDeviceIfExist(self.DeviceType.devicePresence, sensor, sensorsState[sensor], str(sensorsState[sensor]), sensorBatteries[sensor])
    
            cameraState = f.camera(link=Parameters["Mode2"])
            self.updateDeviceIfExist(self.DeviceType.devicePresence, "FREEBOX - Caméra", cameraState, str(cameraState), 100)

            alarmState = f.isAlarmOn()
            alarmBattery = f.getAlarmBattery()
            self.updateDeviceIfExist(self.DeviceType.deviceCommande, "FREEBOX - Alarme", alarmState, str(alarmState), alarmBattery)

            remoteState = f.getRemoteInput()
            remoteBattery = f.getRemoteBattery()
            if(remoteState == 0):
                self.updateDeviceIfExist(self.DeviceType.deviceCommande, "FREEBOX - Télécommande", True, "True", remoteBattery)
            elif(remoteState == 1):
                self.updateDeviceIfExist(self.DeviceType.deviceCommande, "FREEBOX - Télécommande", False, "False", remoteBattery)

        except Exception as e:
            Domoticz.Log("onHeartbeat error: "+str(e))

global _plugin
_plugin = FreeboxPlugin()

def onStart():
    global _plugin
    # on fait une pause de 10 secondes au démarrage pour attendre la Freebox si besoin
    # correction apporté par Gells qui avait des erreur au démarrage
    #https://easydomoticz.com/forum/viewtopic.php?f=10&t=6222&p=55468#p55442
    time.sleep(5)
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
        Domoticz.Debug("Options:         '" + str(Devices[x].Options) + "'")
    return
