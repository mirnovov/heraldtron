CREATE TABLE "armigers" (
	"greii_n" INTEGER NOT NULL PRIMARY KEY,
	"discord_id" INTEGER UNIQUE,
	"qualified_name" TEXT,
	"qualified_id" INTEGER,
	"blazon" TEXT,
);

CREATE TABLE "emblazons" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"url" TEXT
);

CREATE TABLE "guilds" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"limit_commands" INTEGER DEFAULT 0 NOT NULL,
	"sort_channels" INTEGER DEFAULT 0 NOT NULL,
	"welcome_users" INTEGER DEFAULT 0 NOT NULL,
	"welcome_text" TEXT,
	"leave_text" TEXT
);

CREATE TABLE "reddit_feeds" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"guild" INTEGER REFERENCES "guilds"("discord_id") NOT NULL,
	"channel_id" INTEGER NOT NULL,
	"subreddit" TEXT NOT NULL,
	"query" TEXT NOT NULL,
	"last_post" TEXT DEFAULT null
);

CREATE TABLE "roles" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"guild" INTEGER REFERENCES "guilds"("discord_id") NOT NULL,
	"is_admin" INTEGER DEFAULT 1
);

CREATE TABLE "roll_channels" (
	"discord_id" INTEGER PRIMARY KEY,
	"user_id" INTEGER REFERENCES "armigers"("discord_id"),
	"guild_id" INTEGER NOT NULL REFERENCES "guilds"("discord_id")
);

CREATE VIEW "armigers_e" AS 
	SELECT * 
	FROM "armigers" LEFT JOIN "emblazons" 
	ON "armigers"."discord_id" == "emblazons"."id";