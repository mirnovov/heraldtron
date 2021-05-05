import aiohttp, asyncio, functools, io, typing
from ext.seychelles import seychelles
from PIL import Image
from aiohttp.helpers import BaseTimerContext
from aiohttp.http_parser import HttpResponseParserPy

def compute_seychelles(image_url,image):
	seych = OnlineSeych(image_url,image)
	seych.seychelles()
	return seych.save_bytes()

class OnlineSeych(seychelles.Seychelles):
	def __init__(self, url_in, data_in):
		self.name_in = None
		self.ext_in = None 
		self.img_raw = Image.open(data_in)
		self.img_raw = self.img_raw.convert("RGB")
		self.size_in = self.img_raw.size
		self.img_in = self.img_raw.transpose(Image.FLIP_TOP_BOTTOM)
		self.name_out = "seych"
		self.ext_out = "png"
		self.size_out = self.size_in
		self.img_out = Image.new("RGB", self.size_out)
		self.pixels_out = self.img_out.load()
		self.img_print = None
		
	def save_bytes(self):
		if self.img_print is None: raise Exception("No processing done yet")
		outio = io.BytesIO()
		
		self.img_print.save(outio,format="PNG")
		outio.seek(0)
		
		return outio
		
def get_slow_client_session(**kwargs):
	#a horrendous workaround to stop aiohttp breaking on a perfectly fine http request
	#basically replaces HttpResponseParser with its Python fallback
	return aiohttp.ClientSession(connector=_SlowTCPConnector(loop=asyncio.get_running_loop()),**kwargs)	

#---------------------------------------------------------------------------------------------------
# [!]  Modified aiohttp code below.
#	   The following content is a derivative work originally released under the Apache License 2.0,
#      and included in accord with said license's provisions. See this project's LICENSE file, and
#      https://www.apache.org/licenses/LICENSE-2.0.html for more information.
#---------------------------------------------------------------------------------------------------

class _SlowResponseHandler(aiohttp.client_proto.ResponseHandler):
	def set_response_params(
		self, *,
		timer: typing.Optional[BaseTimerContext] = None,
		skip_payload: bool = False,
		read_until_eof: bool = False,
		auto_decompress: bool = True,
		read_timeout: typing.Optional[float] = None,
		read_bufsize: int = 2 ** 16,
	) -> None:
		self._skip_payload = skip_payload
		self._read_timeout = read_timeout
		self._reschedule_timeout()

		self._parser = HttpResponseParserPy(
			self,
			self._loop,
			read_bufsize,
			timer = timer,
			payload_exception = aiohttp.ClientPayloadError,
			response_with_body = not skip_payload,
			read_until_eof = read_until_eof,
			auto_decompress = auto_decompress
		)

		if self._tail:
			data, self._tail = self._tail, b""
			self.data_received(data)
			
class _SlowTCPConnector(aiohttp.connector.TCPConnector):
	def __init__(self,**kwargs):
		super().__init__(**kwargs)
		self._factory = functools.partial(_SlowResponseHandler, loop=kwargs["loop"])
