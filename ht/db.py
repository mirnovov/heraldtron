import aiosqlite, sqlite3

class NvConnection(aiosqlite.Connection):
	async def execute_fetchone(self, query, substs = None):
		cursor = await self.execute(query, substs)
		return await cursor.fetchone()
		
	async def store_get(self, key):
		cursor = await self.execute(f"SELECT value FROM misc_store WHERE key = ?;",(key,))
		return (await cursor.fetchone())[0]
		
	async def store_set(self, key, value):
		await self.execute(f"UPDATE misc_store SET value = ? WHERE key = ?;", (value, key))	
		await self.commit()
	
def connect(database, *, iter_chunk_size = 64, **kwargs):
	return NvConnection(lambda: sqlite3.connect(database, **kwargs), iter_chunk_size)