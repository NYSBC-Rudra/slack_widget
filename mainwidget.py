from PyQt5.QtWidgets import * 
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import * 
from PyQt5.QtGui import * 
import sys
from resolution_calculator import Calculator
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

WINDOW_SIZE = 1000
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Main Window")
		self.setFixedSize(WINDOW_SIZE,WINDOW_SIZE)
		self.calc_newtab = self.createCalculatorWidget()
		self.slack_newtab = self.createSlackWidget()
		all_tabs = QTabWidget()
		all_tabs.setTabPosition(QTabWidget.North)
		all_tabs.addTab(self.calc_newtab, 'calculator')
		all_tabs.addTab(self.slack_newtab, 'support')

		self.setCentralWidget(all_tabs)


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



		





	def createCalculatorWidget(self):
		self.buttonDictionary = {'L': {'picker' : QRadioButton('Caluclate crystal to detector distance')},
			   'd': {'picker': QRadioButton("Calculate resolution")} , 
			   'theta': {'picker':QRadioButton("Calculate detector 2theta")},
			   'wavelength': {'picker':QRadioButton("Calculate wavelength")},
				 'r':{'value':None}}
		
		#making lines to hold inputs 
		self.r_value_enter = QComboBox()
		self.r_value_enter.setToolTip("Choose your detector")
		detectorList = ['NYX-Beamline (200.0mm)?', 'Dectris EIGER2 X 9M (244.7mm)']
		self.r_value_enter.addItems(detectorList)
		self.buttonDictionary['r']['value'] = self.r_value_enter
		self.r_value_enter.setCurrentIndex(1)
		#setting inputs to Double only

		self.L_value_enter = QLineEdit()
		self.L_value_enter.setPlaceholderText('Set L value')
		self.buttonDictionary['L']['value'] = self.L_value_enter
		self.L_value_enter.setValidator(QDoubleValidator())

		self.d_value_enter = QLineEdit()
		self.d_value_enter.setPlaceholderText('Set d value')
		self.buttonDictionary['d']['value'] = self.d_value_enter
		self.d_value_enter.setValidator(QDoubleValidator())

		self.theta_value_enter = QLineEdit()
		self.theta_value_enter.setPlaceholderText('Set theta value')
		self.buttonDictionary['theta']['value'] = self.theta_value_enter
		self.theta_value_enter.setValidator(QDoubleValidator())

		self.wave_value_enter = QLineEdit()
		self.wave_value_enter.setPlaceholderText('Set wavelength value')
		self.buttonDictionary['wavelength']['value'] = self.wave_value_enter
		self.wave_value_enter.setValidator(QDoubleValidator())


		self.final_button = QPushButton('Calculate', self)
		self.final_button.clicked.connect(self.calculateValue)

		self.bottom_text = QLabel()
		self.bottom_text.setText('Enter values and Press button to calculate')


		#creating calculator object
		self.calculator = Calculator()



		layout = QVBoxLayout()
		layout.addWidget(self.r_value_enter)
		for key in self.buttonDictionary:
			if 'picker' in self.buttonDictionary[key].keys(): 
				layout.addWidget(self.buttonDictionary[key]['picker'])
			layout.addWidget(self.buttonDictionary[key]['value'])
		layout.addWidget(self.final_button)
		layout.addWidget(self.bottom_text)
		widget = QWidget(self)
		widget.setLayout(layout)
		return widget

	def createSlackWidget(self):
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
		return widget





	def calculateValue(self):
		checked_key = None
		#checking which formula to use
		for key in self.buttonDictionary:
			if key != 'r' and self.buttonDictionary[key]['picker'].isChecked():
				checked_key = key
		if checked_key == None:
			self.bottom_text.setText("No calculation specified (press one of the radio buttons)")
			return
		
		#getting values from textboxes r_value text box
		r_value = self.r_value_enter.currentIndex()
		convertValues = [200,244.7]
		# print("r value = {}".format(r_value))
		#checking if value is a number string or empty string
		r_value = convertValues[r_value]
		r_value = float(r_value)



		d_value = self.d_value_enter.displayText()
		#checking if value is string or none if not calculating that value (trying to use .isalpha but not when value is None)
		if ((d_value == "" or d_value[0].isalpha() == True) and checked_key != 'd') :
			self.bottom_text.setText("formula to calculate {} requires d value".format(checked_key))
			return

		l_value = self.L_value_enter.displayText()
		if ((l_value == "" or l_value[0].isalpha() == True) and checked_key != 'L'):
			self.bottom_text.setText("formula to calculate {} requires L value".format(checked_key))
			return

		theta_value = self.theta_value_enter.displayText()
		if ((theta_value == "" or theta_value[0].isalpha() == True)and checked_key != 'theta'):
			self.bottom_text.setText("formula to calculate {} requires theta value".format(checked_key))
			return

		wave_value = self.wave_value_enter.displayText()
		if ((wave_value == "" or wave_value[0].isalpha() == True) and checked_key != 'wavelength'):
			self.bottom_text.setText("formula to calculate {} requires the wavelenght".format(checked_key))
			return


		#setting value to return if want value returned
		value_to_return = None

		if checked_key == 'd':
			l_value = float(self.L_value_enter.displayText())
			theta_value = float(self.theta_value_enter.displayText())
			wave_value = float(self.wave_value_enter.displayText())





			variableDict = {'L':l_value, 'theta': theta_value, 'wavelength': wave_value, 'r': r_value}

			self.calculator.set_all_variables(variableDict)
			d_value = self.calculator.calcD()
			value_to_return = d_value
			self.d_value_enter.setText(str(d_value))
			self.calculator.set_variables('d', d_value)




		elif checked_key == 'L':

			D_value = float(self.D_value_enter.displayText())
			theta_value = float(self.theta_value_enter.displayText())
			wave_value = float(self.wave_value_enter.displayText())




			variableDict = {'d':d_value, 'theta': theta_value, 'wavelength': wave_value, 'r': r_value}

			self.calculator.set_all_variables(variableDict)
			L_value = self.calculator.calcL()
			value_to_return = L_value
			self.L_value_enter.setText(str(L_value))
			self.calculator.set_variables('L', L_value)

		elif checked_key == 'theta':

			l_value = float(self.L_value_enter.displayText())
			d_value = float(self.d_value_enter.displayText())
			wave_value = float(self.wave_value_enter.displayText())


			variableDict = {'L':l_value, 'd': d_value, 'wavelength': wave_value, 'r': r_value}

			self.calculator.set_all_variables(variableDict)
			theta_value = self.calculator.calcTheta()
			value_to_return = theta_value
			self.theta_value_enter.setText(str(theta_value))
			self.calculator.set_variables('theta', theta_value)
			


		elif checked_key == 'wavelength':

			l_value = float(self.L_value_enter.displayText())
			theta_value = float(self.theta_value_enter.displayText())
			d_value = float(self.d_value_enter.displayText())
			variableDict = {'L':l_value, 'd': d_value, 'theta': theta_value, 'r': r_value}

			self.calculator.set_all_variables(variableDict)
			wave_value = self.calculator.calcWavelength()
			self.calculator.set_variables('wavelength', wave_value)
			value_to_return = wave_value
			self.wave_value_enter.setText(str(wave_value))
		

		

			



		self.bottom_text.setText("- Done Calculating - \n {} value = {}".format(checked_key, value_to_return))
		return value_to_return


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

window = MainWindow()
window.show()

app.exec()