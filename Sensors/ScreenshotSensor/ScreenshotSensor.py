import os
import pyscreenshot as ImageGrab
from PIL import Image
from Sensors.Sensor import *


TOPIC = 'screenshot'

SCREENSHOT_FILENAME = 'screenshot.png'
scriptFolder = str(os.path.dirname(os.path.realpath(__file__)))


class ScreenshotSensor(Sensor):
    def Initialize(self):
        self.AddTopic(TOPIC)

    def Update(self):
        self.SetTopicValue(TOPIC, self.TakeScreenshot())

    def TakeScreenshot(self):
        filename = os.path.join(scriptFolder, SCREENSHOT_FILENAME)
        ImageGrab.grab().save(filename)
        f = open(filename, "rb")  # 3.7kiB in same folder
        fileContent = f.read()
        image = bytearray(fileContent)
        f.close()
        os.remove(filename)
        return image

    def ManageDiscoveryData(self, discovery_data):
        discovery_data[0]['payload'].pop('state_topic', None)
        discovery_data[0]['payload']['topic']=self.SelectTopic({"topic":TOPIC})
        '''
        discovery_data[0]['payload']['availability']={}
        discovery_data[0]['payload']['availability']['topic']=self.SelectTopic("status")
        discovery_data[0]['payload']['availability']['payload_available']=ONLINE_STATUS
        discovery_data[0]['payload']['availability']['payload_not_available']=OFFLINE_STATUS
        '''
        return discovery_data