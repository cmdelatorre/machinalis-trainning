"""My Simple HTTP Server

Exercise given on the 21/01/2013

"""

import SimpleHTTPServer
import SocketServer
import cgi
import os.path
import time
import datetime

PORT_NUMBER = 8000
ANSWERS_DATA_FILE = "answers.txt"
SUCCESS_PAGE_PATH = "success.html"
FORM_FIELDS = ["firstname", "lastname", "email"]
INVALID_DATA_ERROR_CODE = 409 # Conflict
CANT_SAVE_ERROR_CODE = 500 # Internal Server Error
NOT_MODIFIED_RESPONSE_CODE = 304 # Not Modified http://httpstatusdogs.com/

class MySimpleHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	"""Custom simple HTTP request handler, which validates that 
	some fields are not empty when a POST arrives.

	"""
	def do_GET(self):
		"""If the GET is for the answers (data) file, implement caching control.

		Otherwise, use the nominal do_GET method 
		(from SimpleHTTPServer.SimpleHTTPRequestHandler)

		"""
		if self.path == '/'+ANSWERS_DATA_FILE:
			self.answers_data_caching_control()
		else:
			SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

	def do_POST(self):
		"""If the POST is on the quetions form, validate the form's data
		and save it to an answers (data) file.

		"""
		if self.path=="/save":
			data = self.extract_form_data()
			is_ok, msg = self.validate_form_data(data)
			if is_ok:
				try:
					self.save_data_to_file(data, ANSWERS_DATA_FILE)
					self.redirect_to_success_page()
				except IOError:
					self.send_error_response(
							CANT_SAVE_ERROR_CODE,
							"Couldn't save the file"
							)
			else:
				self.send_error_response(INVALID_DATA_ERROR_CODE, msg)
			# Valid data. Continue with nominal.

	def extract_form_data(self):
		"""Extract the firstname, lastname and email from the questions form,
		input by the user. Return a dict with such keys.

		"""
		form = cgi.FieldStorage(
			fp=self.rfile, 
			headers=self.headers,
			environ={'REQUEST_METHOD':'POST',
	                 'CONTENT_TYPE':self.headers['Content-Type'],
		})
		form_data = {}
		for k in FORM_FIELDS:
			value = ''
			if form.has_key(k):
				value = form[k].value
			else:
				print "no tiene",k
			form_data[k] = value
		# Other checks here, like email format, etc.
		return form_data

	def validate_form_data(self, data):
		"""Validate the data. 'data' must be a dict.

		Return (True, '') if the data is valid, (False, msg) otherwise,
		where 'msg' is a descriptive message of the error.

		"""
		ret_val = (True, '')
		for k in data.keys():
			if len(data[k]) == 0:
				ret_val = (False, 'Empty field: %s'%k)
				break
		return ret_val

	def save_data_to_file(self, data, fname):
		"""Save the 'data' in the 'fname' file, as 'key = value' pairs.

		Overwrites the data file if already exists. May raise IOError.

		"""
		data_file = open(fname, 'w')
		data_file.write(
				"first name = %s\nlast name = %s\nemail = %s"\
				%(data["firstname"], data["lastname"], data["email"])
				)
		data_file.close()

	def redirect_to_success_page(self):
		"""Send a 302 response (Found) and redirect to the success page."""
		self.send_response(302, "Data saved.")
		self.send_header("Location", SUCCESS_PAGE_PATH)
		self.end_headers()

	def send_error_response(self, error_code, message):
		self.send_error(error_code)
		self.send_header("Content-Type", "text/html")
		self.end_headers()
		self.wfile.write(self.render_error_message(message))
		
	def render_error_message(self, msg):
		""""""
		return "<head></head><body><b>"+msg+"</b></body>"

	def answers_data_caching_control(self):
		"""Implement the cache control on the answer's data file.

		If the request includes an If-Modified-Since header, the data file's
		modification time is verified. If it hasn't been modified, a 
		'Not modified' response is sent. Otherwise, the data is sent.

		"""
		data_fname = os.path.abspath(ANSWERS_DATA_FILE)
		last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(data_fname))
		client_modif_time = None
		if self.headers.has_key("If-Modified-Since"):
			print self.headers
			try:
				client_modif_time = datetime.datetime.strptime(
						self.headers["If-Modified-Since"], '%Y-%m-%d %H:%M:%S.%f'
						)
			except ValueError:
				client_modif_time = None
		
		if client_modif_time is not None and\
				last_modified <= client_modif_time:
			# Not modified. Don't send.
			print "Not modified. Code", NOT_MODIFIED_RESPONSE_CODE
			self.send_response(NOT_MODIFIED_RESPONSE_CODE)
		else:
			# print "NEWER IN SERVER. Deliver the file."
			print "Modified. Send the file."
			self.deliver_data_file(last_modified, data_fname)

	def deliver_data_file(self, last_modified, data_fname):
		"""Deliver the answer's data in a response contents.

		May rise IOError if the data file can't be read.

		"""
		self.send_response(200)
		#self.send_header("Location", SUCCESS_PAGE_PATH)
		size = os.path.getsize(data_fname)
		self.send_header("Content-Type", "text/plain")
		self.send_header("Content-Length", size)
		self.send_header("Last-Modified", last_modified)
		#self.send_header("Server", "localhost")
		self.send_header("Date", self.date_time_string())
		#self.send_header("Cache-Control", "public") # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9
		#self.send_header("Content-Range", "") # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.16
		self.end_headers()
		self.wfile.write(open(data_fname).read())


if __name__ == "__main__":
	try:
		server = SocketServer.TCPServer(("", PORT_NUMBER), MySimpleHTTPRequestHandler)
		print "serving at port", PORT_NUMBER
		server.serve_forever()
	except KeyboardInterrupt:
		print ' shutting down the web server'
		server.socket.close()