import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, QObject, pyqtSlot, pyqtSignal
import sys
from slack_sdk import WebClient
from slack_sdk.rtm_v2 import RTMClient
import json
import os


class SlackMonitor(QObject):
    slack_signal = pyqtSignal(str)
    

    #ADD TOKEN TO OauthTokens.json
    with open('OauthTokens.json') as token_data:
        tokens = json.load(token_data)
        
    real_time_messaging = RTMClient(token= tokens['Test-Auth'])

    def __init__(self):
        super().__init__()
        self.variable_text = None
        #NYX_LSDC_SUPPORT_CHANNEL = 'C0541P8BR8T'
        #test_channel = 'C055AMMLPNJ'
        self.channel = 'C055AMMLPNJ'


    def startMonitor(self):
        self.real_time_messaging.start()



    # @real_time_messaging.on("message")
    # def handle(client: RTMClient, event: dict):
    #     print('hi')
    #     self.slack_signal.emit(event['text'])



    


    @pyqtSlot(str)
    def sendToSlack(self, str_to_send, rtm = real_time_messaging):
        #print(str_to_send)
        rtm.web_client.chat_postMessage(
            channel=self.channel,
            text = str_to_send
        )
        
        







class MainChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")
        self.setFixedSize(800,500)

        #making text fields
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.sendMessage)
        layout = QVBoxLayout()
        #adding to widget
        layout.addWidget(self.text_area)
        layout.addWidget(self.message_input)
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)


        #connecting to slack connector
        self.slackChecker = SlackMonitor()

        self.thread = QThread(self)
        #connect slackmonitor variable to self.printString
        self.slackChecker.slack_signal.connect(self.printString)
        self.slackChecker.moveToThread(self.thread)
        self.thread.started.connect(self.slackChecker.startMonitor)
        self.message_input.returnPressed.connect(self.sendtoslackhelper)


        #naming for users in app
        #could scan channel to look for user-name combinations and make a dictionary from that
        self.nameDictionary = {'U054RHJQ7C0':'Kevin Bataille', 'U058G0XUEKY':'Rudra Subramanian', 'U055H9YBP1Q':'Rudra Subramanian' }


        self.thread.start()

    
        @self.slackChecker.real_time_messaging.on("message")
        def handle(client: RTMClient, event: dict):
            if event['channel'] == self.slackChecker.channel:
                self.printString(event['text'], event['user'])
                print('hello')
            

    @pyqtSlot(str)
    def printString(self, stringpath, user):
        text_format = "<span style='background-color:green;'>{}</span>"
        if user in self.nameDictionary.keys():
            self.updateScreen(stringpath, self.nameDictionary[user], text_format)
        else:
            self.updateScreen(stringpath, 'support', text_format)

        
    def sendtoslackhelper(self):
        if self.message_input.text() == '':
            return
        self.slackChecker.sendToSlack(self.message_input.text())
        self.message_input.clear()


    def printtext(self):
        print(self.message_input.text())
        
    def sendMessage(self):
        text_format = '<span style="background-color:gray;">{}</span>'
        #server.post(self.message_input.text())
        self.updateScreen(self.message_input.text(), 'Me', text_format)
        
        pass

    def updateScreen(self,message,user, text_format):
        print('hello')
        message = '{}: {}'.format(user, message)
        self.text_area.append(text_format.format(message))




          
app = QApplication(sys.argv)
window = MainChatWindow()
window.show()
app.exec()