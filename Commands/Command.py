from consts import *
import Logger
from Configurator import Configurator
import sys
import yaml
from os import path


class Command():

    def __init__(self, monitor_id, brokerConfigs, mqtt_client, commandConfigs, logger, commandManager):  # Config is args
        self.name = self.GetCommandName()
        self.options = {}
        self.monitor_id = monitor_id
        self.brokerConfigs = brokerConfigs
        self.mqtt_client = mqtt_client
        self.commandConfigs = commandConfigs
        self.commandManager = commandManager
        self.logger = logger
        self.subscribedTopics = 0

        # Get for some features the pathof the folder cutting the py filename (abs path to avoid windows problems)
        self.commandPath = path.dirname(path.abspath(
            sys.modules[self.__class__.__module__].__file__))

        self.ParseOptions()
        self.Initialize()

    # Implemented in sub-classes
    def Initialize(self):
        pass

    def PostInitialize(self):  # Implemented in sub-classes
        pass

    def CallCallback(self, message):  # Safe method to run the Callback
        try:
            self.Log(Logger.LOG_INFO, 'Command actioned')
            self.Callback(message)
        except Exception as exc:
            self.Log(Logger.LOG_ERROR, 'Error occured in callback: '+str(exc))
            self.Log(Logger.LOG_ERROR, Logger.ExceptionTracker.TrackString(exc))
            self.commandManager.UnloadCommand(self.name, self.monitor_id)

    # Implemented in sub-classes
    def Callback(self, message):  # Run by the OnMessageEvent
        pass

    def PublishDiscoveryData(self):
        pass

    def ParseOptions(self):
        # I can have options both in broker configs and single command configs
        # At first I search in broker config. Then I check the per-command option and if I find
        # something there, I replace - if was set from first step -  broker configs (or simply add a new entry)

        for optionToSearch in POSSIBLE_OPTIONS:
            # 1: Set from broker's configs
            if optionToSearch in self.brokerConfigs:
                self.options[optionToSearch] = self.brokerConfigs[optionToSearch]

            # 2: Set from command's configs
            if self.commandConfigs and optionToSearch in self.commandConfigs:
                self.options[optionToSearch] = self.commandConfigs[optionToSearch]


    def GetOption(self, path,defaultReturnValue=None):
        return Configurator.GetOption(self.options,path,defaultReturnValue)
        

    def FindCommand(self, name):  # Find active commands for some specific action
        if(self.commandManager):
            return self.commandManager.FindCommand(name, self.monitor_id)
        else:
            self.Log(Logger.LOG_ERROR, 'CommandManager not set in the command!')

        return None

    def FindSensor(self, name):  # Find active sensors for some specific action
        if(self.commandManager):
            if(self.commandManager.sensorManager):
                return self.commandManager.sensorManager.FindSensor(name, self.monitor_id)
            else:
                self.Log(Logger.LOG_ERROR,
                         'CommandManager not set in the SensorManager!')
        else:
            self.Log(Logger.LOG_ERROR, 'CommandManager not set in the command!')

        return None

    def SubscribeToTopic(self, topic):
        self.subscribedTopics += 1

        # If user in options defined custom topics, use them and not the one choosen in the command
        if self.GetOption(CUSTOM_TOPICS_OPTION_KEY) and len(self.GetOption(CUSTOM_TOPICS_OPTION_KEY)) >= self.subscribedTopics:
            topic = self.GetOption(CUSTOM_TOPICS_OPTION_KEY)[
                self.subscribedTopics-1]
            self.Log(Logger.LOG_INFO, 'Using custom topic defined in options')

        self.mqtt_client.AddNewTopic(topic, self)

        # Log the topic as debug if user wants
        if self.GetOption(DEBUG_OPTION_KEY):
            self.Log(Logger.LOG_DEBUG, 'Subscribed to topic: ' + topic)

        return topic  # Return the topic cause upper function should now that topic may have been edited

    def GetTopic(self, last_part_of_topic):
        model = TOPIC_FORMAT
        if 'topic_prefix' in self.brokerConfigs:
            model = self.brokerConfigs['topic_prefix'] + \
                '/'+model
        return model.format(self.brokerConfigs['name'], last_part_of_topic)

    def GetClassName(self):
        # Command.SENSORFOLDER.SENSORCLASS
        return self.__class__.__name__

    def GetCommandName(self):
        # Only SENSORCLASS (without Command suffix)
        return self.GetClassName().split('.')[-1].split('Command')[0]

    def GetMqttClient(self):
        return self.mqtt_client

    def GetLogger(self):
        return self.logger

    def GetMonitorID(self):
        return self.monitor_id

    def LoadRequirements(self):
        # 1: Get path of the single object
        # 2: If I dont find the yaml in that folder, I return None
        # 3: If I find it, I parse the yaml and I return the dict
        # Start:
        # 1
        requirements_path = path.join(
            self.commandPath, OBJECT_SETTINGS_FILENAME)
        # try 3 except 2
        try:
            with open(requirements_path) as f:
                return yaml.load(f, Loader=yaml.FullLoader)
        except:
            return None

    def Log(self, messageType, message):
        self.logger.Log(messageType, self.name+' Command', message)
