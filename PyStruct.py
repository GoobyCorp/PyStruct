from enum import IntEnum
from struct import pack_into, unpack_from

class Endian(IntEnum):
	LITTLE = 0
	BIG = 1

class StructType(IntEnum):
	UINT8 = 0
	UINT16 = 1
	UINT32 = 2
	UINT64 = 3

	INT8 = 4
	INT16 = 5
	INT32 = 6
	INT64 = 7

	FLOAT32 = 8
	FLOAT64 = 9

	BOOL = 10

class Structure:
	fields = []
	size = 0
	buffer = b""
	endian = "<"
	lookup = {}

	def __init__(self, endian: Endian = Endian.LITTLE):
		self.reset()
		self.preprocess()
		self.set_endian(endian)
		self.buffer = bytearray(self.size)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.reset()

	def __getitem__(self, item):
		if item in self.lookup:
			return self.get_struct_value(item)
		super(Structure, self).__getitem__(item)

	def __setitem__(self, key, value):
		if key in self.lookup:
			self.set_struct_value(key, value)
			return
		super(Structure, self).__setitem__(key, value)

	def __bytes__(self) -> bytes:
		return bytes(self.buffer)

	def reset(self) -> None:
		# self.fields = []
		self.size = 0
		self.buffer = b""
		self.endian = "<"
		self.lookup = {}
		self.index = 0

	def set_endian(self, endian: Endian) -> None:
		return ("<", ">")[int(endian)]

	def load_buffer(self, data: (bytes, bytearray)) -> None:
		assert len(data) == self.size, "Data size doesn't match the calculated structure size"
		self.buffer = bytearray(data)

	def copy_buffer(self, data: (bytes, bytearray), index: int) -> None:
		pack_into(f"{len(data)}s", self.buffer, index, data)

	@staticmethod
	def create(data: (bytes, bytearray), endian: Endian = Endian.LITTLE):
		s = Structure(endian)
		s.load_buffer(data)
		return s

	def get_struct_value(self, key: str):
		(index, size, count, t) = self.lookup[key]
		tt = self._translate_type(t)
		if t == StructType.UINT8 and count > 1:
			tt = "s"
		value = unpack_from(self.endian + str(count) + tt, self.buffer, index)
		if len(value) == 1:
			return value[0]
		return value

	def set_struct_value(self, key: str, value):
		(index, size, count, t) = self.lookup[key]
		#if t == StructType.UINT8ARRAY and len(value) < count:
		#	tmp = bytearray(count)
		#	pack_into(self.endian + str(count) + self._translate_type(t), tmp, 0, value)
		#	value = tmp
		tt = self._translate_type(t)
		if t == StructType.UINT8 and count > 1:
			tt = "s"
		if isinstance(value, list) or isinstance(value, tuple):
			pack_into(self.endian + str(count) + tt, self.buffer, index, *value)
		else:
			pack_into(self.endian + str(count) + tt, self.buffer, index, value)

	def preprocess(self) -> None:
		for single in self.fields:
			e = 1
			if len(single) == 2:
				(k, t) = single
			elif len(single) == 3:
				(k, t, e) = single
			else:
				raise Exception("Invalid field definition size")

			if t in (StructType.UINT8, StructType.INT8, StructType.BOOL):
				item_size = 1
			elif t in (StructType.UINT16, StructType.INT16):
				item_size = 2
			elif t in (StructType.UINT32, StructType.INT32):
				item_size = 4
			elif t in (StructType.UINT64, StructType.INT64):
				item_size = 8
			elif t == StructType.FLOAT32:
				item_size = 4
			elif t == StructType.FLOAT64:
				item_size = 8
			else:
				raise Exception("Invalid type in field definition")
			self.lookup[k] = (self.size, item_size, e, t)
			self.size += item_size * e

	def _translate_type(self, t: StructType) -> str:
		if t in (StructType.UINT8, StructType.INT8,):
			return "B" if t == StructType.UINT8 else "b"
		elif t in (StructType.UINT16, StructType.INT16,):
			return "H" if t == StructType.UINT16 else "h"
		elif t in (StructType.UINT32, StructType.INT32,):
			return "I" if t == StructType.UINT32 else "i"
		elif t in (StructType.UINT64, StructType.INT64,):
			return "Q" if t == StructType.UINT64 else "q"
		elif t == StructType.FLOAT32:
			return "f"
		elif t == StructType.FLOAT64:
			return "d"
		elif t == StructType.BOOL:
			return "?"