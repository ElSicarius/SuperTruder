
import jwt

def process(payload):
	if isinstance(payload, bytes):
		try:
			payload = payload.decode("utf8")
		except UnicodeDecodeError:
			# woops, can't decode your payload, I can't do better than that:
			payload = str(payload)[2:-1]
	payload = jwt.encode(\
						# change the json according to your jwt setup
						{"id": "1", "name":"test","description":payload,"email":"thisisatest@test.test"},\
						# Enter your key below
						'example_key',\
						# change the algorithm if needed
						algorithm='HS256').decode()
	return payload