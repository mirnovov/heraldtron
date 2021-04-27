CREATE TABLE "armigers" (
	"greii_n" INTEGER NOT NULL PRIMARY KEY,
	"discord_id" INTEGER UNIQUE,
	"qualified_name" TEXT,
	"qualified_id" INTEGER,
	"blazon" TEXT UNIQUE,
	"emblazon_url" TEXT UNIQUE
);


CREATE TABLE "guilds" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"type" INTEGER DEFAULT 0 NOT NULL,
	"warning_channel" INTEGER UNIQUE,
	"welcome_users" INTEGER,
	"welcome_text" TEXT,
	"leave_text" TEXT
);


CREATE TABLE "roles" (
	"discord_id" INTEGER PRIMARY KEY,
	"name" TEXT NOT NULL,
	"guild" INTEGER REFERENCES "guilds"("discord_id") NOT NULL,
	"is_admin" INTEGER DEFAULT 'true'
);


CREATE TABLE "roll_channels" (
	"discord_id" INTEGER PRIMARY KEY,
	"user_id" INTEGER REFERENCES "armigers"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"type" INTEGER DEFAULT 2 NOT NULL,
	"guild_id" INTEGER NOT NULL REFERENCES "guilds"("discord_id") NOT DEFERRABLE INITIALLY IMMEDIATE,
	"archived" INTEGER NOT NULL DEFAULT 'false',
	"never_archive" INTEGER NOT NULL DEFAULT 'false'
);


CREATE TABLE "warnings" (
	"id" INTEGER PRIMARY KEY ASC AUTOINCREMENT,
	"issuer_id" INTEGER NOT NULL,
	"target_id" INTEGER NOT NULL,
	"reason" TEXT NOT NULL,
	"time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);