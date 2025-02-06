import aiohttp, asyncio, functools, io, typing
from ext.seychelles import seychelles
from ext.sql import AioSqliteConnectionAdapter

from PIL import Image
from aiohttp.helpers import BaseTimerContext
from aiohttp.http_parser import HttpResponseParserPy

class OnlineSeych(seychelles.Seychelles):
	def __init__(self, url_in, data_in):
		self.name_in = None
		self.ext_in = None

		with Image.open(data_in) as img:
			self.img_raw = img.convert("RGB")
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

		self.img_print.save(outio, format = "PNG")
		outio.seek(0)

		return outio

	@staticmethod
	def generate(image_url, image):
		seych = OnlineSeych(image_url, image)
		seych.seychelles()
		return seych.save_bytes()
