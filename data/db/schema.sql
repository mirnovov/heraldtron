CREATE TABLE "armigers" (
	"greii_n" INTEGER NOT NULL PRIMARY KEY,
	"discord_id" INTEGER UNIQUE,
	"qualified_name" TEXT,
	"discrim_upgraded" INTEGER NOT NULL DEFAULT 0,
	"blazon" TEXT
);

CREATE TABLE "channels" (
	"discord_id" INTEGER PRIMARY KEY,
	"guild" INTEGER REFERENCES "guilds"("discord_id") NOT NULL,
	"proposal" INTEGER DEFAULT 0 NOT NULL,
	"oc" INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE "emblazons" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"url" TEXT
);

CREATE TABLE "guilds" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"limit_commands" INTEGER DEFAULT 0 NOT NULL,
	"roll" INTEGER DEFAULT 0 NOT NULL,
	"welcome_users" INTEGER DEFAULT 0 NOT NULL,
	"welcome_text" TEXT,
	"leave_text" TEXT,
	"log" INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE "misc_store" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"key" TEXT NOT NULL UNIQUE,
	"value" TEXT DEFAULT NULL
);

INSERT INTO "misc_store" (key, value) VALUES
	("book_timestamp", "0"),
	("last_avatar", "0");

CREATE TABLE "reddit_feeds" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"guild" INTEGER REFERENCES "guilds"("discord_id") NOT NULL,
	"channel_id" INTEGER NOT NULL,
	"subreddit" TEXT NOT NULL,
	"ping" INTEGER DEFAULT 0,
	"query" TEXT NOT NULL,
	"last_post" TEXT DEFAULT NULL
);

CREATE TABLE "roll_channels" (
	"discord_id" INTEGER PRIMARY KEY,
	"user_id" INTEGER REFERENCES "armigers"("discord_id"),
	"guild_id" INTEGER NOT NULL REFERENCES "guilds"("discord_id"),
	"personal" INTEGER DEFAULT 0,
	"name" TEXT
);

CREATE VIEW "armigers_e" AS
	SELECT *
	FROM "armigers" LEFT JOIN "emblazons"
	ON "armigers"."discord_id" == "emblazons"."id";
