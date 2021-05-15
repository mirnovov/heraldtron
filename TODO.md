#Before release
- Implement DB stuff
	- Maybe add auto roll channel setup (might be helpful, as mods often get the perms slightly wrong)
	- Finish roll channel autocategorisation/archiving (see sort.py for exact todo)
		- channel sorting behaviour from discord-ext-alternatives?
	- Possibly show appropriate roll channels on armiger command
	- Make functionality currently unusable in DMs available where possible
	- Add proper mod authorisation (using _roles if viable for efficiency)

#Long term/later
- Make a 3.7 branch and try optimized Python implementations, such as Pyston, Nuitka, or PyPy
- Add task that checks every 24 hours and updates status to random
	- On appropriate days of the year, changes the pfp and status thematically