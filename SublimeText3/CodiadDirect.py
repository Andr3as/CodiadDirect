import sublime, sublime_plugin, threading, re, os
from . import requests
from .requests.auth import HTTPBasicAuth

timeout  = 20
verify   = True

class CodiadDirectCommand(sublime_plugin.TextCommand):
	def run(self, edit, action):
		self.edit   = edit
		self.action = action

		self.session = None

		self.login  = False
		self.buffer = []
		self.data	= []
		self.path   = ""

		self.username = ""
		self.password = ""
		self.codiad_url = ""
		self.basic_username = ""
		self.basic_password = ""
		self.basic_authentication = False

		self.window = self.view.window()
		self.loadSettings()
		
		self.checkCodiadUrl()

	def openFile(self):
		self.getUsername()
		

	def saveFile(self):
		self.getUsername()

	def checkCodiadUrl(self):
		if self.basic:
			callback = self.getBasicUsername
		else:
			callback = self.getUsername
		if not self.codiad_url == "":
			callback()
		else:
			self.window.show_input_panel('Insert the location of your Codiad installation:', 'https://', callback, None, None)

	def getUsername(self, codiad_url = None):
		if self.codiad_url == "":
			self.codiad_url = codiad_url
		if not self.username == "":
			self.getPassword()
		else:
			self.window.show_input_panel('Insert your codiad username:', '', self.getPassword, None, None)

	def getPassword(self, username = None):
		if self.username == "":
			self.username = username
		if not self.password == "":
			self.getUserProjects()
		else:
			self.window.show_input_panel('Insert your codiad password:', '', self.setPassword, None, None)

	def getBasicUsername(self, codiad_url = None):
		if self.codiad_url == "":
			self.codiad_url = codiad_url
		if not self.basic_username == "":
			self.getBasicPassword()
		else:
			self.window.show_input_panel('Insert your basic username:', '', self.getBasicPassword, None, None)

	def getBasicPassword(self, basic_username = None):
		if self.basic_username == "":
			self.basic_username = basic_username
		if not self.basic_password == "":
			self.getUsername()
		else:
			self.window.show_input_panel('Insert your basic password:', '', self.setBasicPassword, None, None)

	def setBasicPassword(self, basic_password):
		self.basic_password = basic_password
		self.getUsername()

	def setPassword(self, password):
		if self.password == "":
			self.password = password
		self.getUserProjects()

	def authenticate(self, result = None):
		if not result == None:
			if not result['status'] == 'error':
				self.login = True
			else:
				sublime.status_message('Failed to login')
				return
		if self.login:
			self.getUserProjects()
		else:
			data = {'username': self.username, 'password': self.password, 'language': 'de', 'theme': 'default'}
			self.startRequest(self.codiad_url + '/components/user/controller.php?action=authenticate', self.authenticate, data)

	def getUserProjects(self):
		if not self.login:
			self.authenticate()
			return
		self.startRequest(self.codiad_url + '/plugins/CodiadDirect/controller.php?action=getUserProjects', self.listUserProjects)

	def listUserProjects(self, result):
		if result['status'] == 'error':
			sublime.status_message('Failed to get User projects')
			return
		else:
			projects = []
			self.buffer = result['projects']
			for k in result['projects']:
				projects.append(k.get('name'))
			if len(projects):
				self.show_quick_panel(projects, self.userProjectSelected)
			else:
				sublime.status_message('User has no projects')

	def userProjectSelected(self, index):
		if index == -1:
			print("canceld")
			return
		self.path = self.buffer[index].get('path')
		self.getFiles(self.path)
	
	def listItems(self, result):
		self.buffer = result['data']['index']
		self.data = ['..', '.']
		for k in self.buffer:
			self.data.append(k.get('name'))
		if len(self.data):
			self.show_quick_panel(self.data, self.itemSelected)
		else:
			self.path = self.dirname(self.path)
			self.getFiles(self.path)

	def itemSelected(self, index):
		if index == -1:
			print("canceld")
			return
		# Reduce index by one, because buffer does not contains ..
		index = index - 2
		if self.data[index + 2] == '..':
			self.path = self.dirname(self.path)
			self.getFiles(self.path)
			return
		if self.data[index + 2] == '.':
			if self.action == 'save_file':
				self.getFilename(self.path)
			else:
				self.getFiles(self.path)
			return
		self.path = self.buffer[index].get('name')
		if self.action == 'open_file':
			if self.buffer[index].get('type') == 'file':
				self.openFile(self.path)
				return
			if self.buffer[index].get('type') == 'directory':
				self.getFiles(self.path)
				return
		if self.action == 'save_file':
			if self.buffer[index].get('type') == 'directory':
				self.getFilename(self.path)
				return
			if self.buffer[index].get('type') == 'file':
				self.saveFile()
				return

	def getFiles(self, path):
		if path == "":
			self.getUserProjects()
			return
		self.startRequest(self.codiad_url + '/components/filemanager/controller.php?action=index&path=' + path, self.listItems)

	def openFile(self, path):
		self.startRequest(self.codiad_url + '/components/filemanager/controller.php?action=open&path=' + path, self.insertContent)

	def insertContent(self, result):
		if result['status'] == 'error':
			sublime.status_message('Failed to get User projects')
			return
		else:
			self.view.run_command('codiad_direct_insert', {'content': result['data']['content'], 'path': self.path})


	def getFilename(self, path):
		self.path = path
		view = self.window.active_view()
		name = view.name()
		print(name)
		if name == None:
			name = ""
		else:
			name = self.getName(name)
			print(name)
		self.window.show_input_panel('Enter Filename:', name, self.saveFile, None, None)

	def saveFile(self, name = None):
		if not name == None:
			self.path = self.path + "/" + name
		view    = self.window.active_view()
		content = view.substr(sublime.Region(0, view.size()))
		self.startRequest(self.codiad_url + '/plugins/CodiadDirect/controller.php?action=saveFile&path=' + self.path, self.requestResult, {'content': content})

	def requestResult(self, result):
		sublime.status_message(result['message'])
		print(result)
			

	def dirname(self, path):
		dirname = re.sub(r"\\", "/", path)
		dirname = re.sub(r"\/[^\/]*\/?$", "", dirname)
		if path == dirname:
			return ""
		else:
			return dirname

	def getName(self, path):
		dirname = self.dirname(path)
		if dirname == "":
			return path
		dirname = dirname + "/"
		path    = path.replace(dirname, "")
		return path

	def getExtension(self, path):
		f, e = os.path.splitext(path)
		
		if e[:1] == ".":
			e = e[1:]
		return e

	def loadSettings(self):
		# load settings
		self.settings = sublime.load_settings('CodiadDirect.sublime-settings')
		
		self.username = self.settings.get('codiad_username', "")
		self.password = self.settings.get('codiad_password', "")
		self.codiad_url = self.settings.get('codiad_url', "")
		globals()['timeout']  = self.settings.get('timeout', 20)
		globals()['verify']   = self.settings.get('ssl_verify', True)
		self.basic = self.settings.get('basic_authentication', False)
		if self.basic:
			self.basic_username = self.settings.get('basic_username', "")
			self.basic_password	= self.settings.get('basic_password', "")

	def show_quick_panel(self, messages, callback = None):
		self.window.show_quick_panel(messages, callback, sublime.MONOSPACE_FONT)

	def startRequest(self, url, callback, data = None):
		print(url)
		if self.basic:
			thread = ApiCall(url, data, self.basic_username, self.basic_password)
			print("basic")
		else:
			thread = ApiCall(url, data)
		if self.session == None:
			self.session = requests.Session()
		thread.s = self.session
		thread.start()

		self.handle_thread(thread, callback)

	def is_st3():
		return sublime.version()[0] == '3'

	def handle_thread(self, thread, callback, offset=0, i=0, dir=1):
		if thread.is_alive():
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			self.view.set_status('codiad', 'CodiadDirect [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_thread(thread, callback, offset, i, dir), 100)
			return
		elif thread.result == False:
			print(thread.error)
			sublime.status_message(thread.error)
		else:
			print(thread.result)
			callback(thread.result)
		self.view.erase_status('codiad')

class ApiCall(threading.Thread):
	
	s = None

	def __init__(self, url, data, user = None, password = None):
		self.result  = None
		self.error	 = ""
		self.url     = url
		self.data    = data
		self.timeout = timeout
		self.verify	 = verify
		self.user 	 = user
		self.password= password
		self.counter = 0
		threading.Thread.__init__(self)

	def run(self):
		if self.data == None:
			payload = {}
		else:
			payload = self.data
		try:
			if not self.user == None and not self.password == None:
				r = self.s.post(self.url, data=payload, timeout=self.timeout, verify=self.verify, auth=HTTPBasicAuth(self.user, self.password))
			else:
				r = self.s.post(self.url, data=payload, timeout=self.timeout, verify=self.verify)
			if not r.status_code == 200:
				self.error  = "HTTP Status Code: " + str(r.status_code)
				self.result = False
				return

			print(r.text)
			self.result = r.json()
			return
		except Exception as e:
			if str(e) == "('Connection aborted.', BadStatusLine('',))":
				if self.counter < 2:
					print("rerun")
					self.counter = self.counter + 1
					self.run()
					return
			self.error  = str(e)
			self.result = False
			return

class CodiadDirectInsertCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		view = self.view.window().new_file()
		view.insert(edit, 0, args['content'])
		view.set_name(args['path'])