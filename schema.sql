CREATE TABLE "armigers" (
	"discord_id" INTEGER PRIMARY KEY,
	"greii_n" INTEGER NOT NULL UNIQUE,
	"qualified_name" TEXT,
	"qualified_id" INTEGER,
	"blazon" TEXT UNIQUE,
	"emblazon_url" TEXT UNIQUE
);


CREATE TABLE "guilds" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"type" INTEGER DEFAULT 0 NOT NULL,
	"welcome_channel" INTEGER UNIQUE,
	"warning_channel" INTEGER UNIQUE
);


CREATE TABLE "roll_channels" (
	"discord_id" INTEGER PRIMARY KEY,
	"user_id" INTEGER REFERENCES "armigers"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"type" INTEGER DEFAULT 2 NOT NULL,
	"guild_id" INTEGER NOT NULL REFERENCES "guilds"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"archived" BOOLEAN NOT NULL DEFAULT 'false',
	"never_archive" BOOLEAN NOT NULL DEFAULT 'false'
);


CREATE TABLE "warnings" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"issuer_id" INTEGER NOT NULL,
	"target_id" INTEGER NOT NULL,
	"reason" TEXT NOT NULL,
	"time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
