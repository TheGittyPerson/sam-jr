# SpotifyAdMuter Junior (SAM Jr.)

Better, simpler, and more energy/CPU efficient version of [SAM].
Original SAM runs Applescript thousands of times per hour and can use more 
than 100% of your battery in 12 hours if running continuously. This one
watches `~/Library/Application Support/Spotify/Users/*-user/ad-state-storage.bnk`
for changes and calls Applescript only then, similar to [this].

Cons: designed for my personal use. If you want to configure things you'll 
need to edit the script yourself.

[SAM]: https://github.com/TheGittyPerson/SpotifyAdMuter
[this]: https://github.com/qmnl/MuteSpotifyAds
