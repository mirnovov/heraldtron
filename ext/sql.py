import aiosqlite, collections, contextlib, sqlite3
from jishaku.features.sql import Adapter

class AioSqliteConnectionAdapter(Adapter):
	def __init__(self, connection):
		super().__init__(connection)
		self.connection = None
	
	@contextlib.asynccontextmanager
	async def use(self):
		if not self.connector.row_factory: 
			self.connector.row_factory = aiosqlite.Row
		
		self.connection = self.connector
		yield
	
	def info(self) -> str:
		return f"aiosqlite {aiosqlite.__version__} {type(self.connector).__name__}"
	
	async def fetchrow(self, query):
		row = await self.connection.execute_fetchone(query)
		return dict(row) if row else None
	
	async def fetch(self, query):
		return [dict(row) for row in await self.connection.execute_fetchall(query)]
	
	async def execute(self, query):
		return str((await self.connection.execute(query)).rowcount)
	
	async def table_summary(self, table_query):
		tables = collections.defaultdict(dict)
	
		if table_query:
			for row in await self.connection.execute_fetchall(
				"SELECT name, type, `notnull`, dflt_value, pk from pragma_table_info(?);",
				(table_query,)
			):
				tables[table_query][row["name"]] = self.format_column_row(row)
	
		else:
			for row in await self.connection.execute_fetchall("SELECT name FROM sqlite_master WHERE type = 'table';"):
				name = row['name']
	
				for table_column in await self.connection.execute_fetchall(
					"SELECT name, type, `notnull`, dflt_value, pk from pragma_table_info(?);",
					(name,)
				):
					tables[name][table_column["name"]] = self.format_column_row(table_column)
	
		return tables
	
	def format_column_row(self, row):
		default = row["dflt_value"]
		not_null = " NOT NULL" if row["notnull"] == 1 else ""
		default_value = f" DEFAULT {default}" if default else ""
		primary_key = " PRIMARY KEY" if row["pk"] else ""
	
		return f"{row["type"]}{not_null}{default_value}{primary_key}"
