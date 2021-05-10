CREATE TABLE "armigers" (
	"greii_n" INTEGER NOT NULL PRIMARY KEY,
	"discord_id" INTEGER UNIQUE,
	"qualified_name" TEXT,
	"qualified_id" INTEGER,
	"blazon" TEXT
);

CREATE TABLE "emblazons" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"greii_n" INTEGER REFERENCES "armigers"("greii_n"),
	"url" TEXT
);

CREATE TABLE "guilds" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"type" INTEGER DEFAULT 0 NOT NULL,
	"welcome_users" INTEGER,
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
	"user_id" INTEGER REFERENCES "armigers"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"type" INTEGER DEFAULT 2 NOT NULL,
	"guild_id" INTEGER NOT NULL REFERENCES "guilds"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"archived" INTEGER NOT NULL DEFAULT 0,
	"never_archive" INTEGER NOT NULL DEFAULT 0
);