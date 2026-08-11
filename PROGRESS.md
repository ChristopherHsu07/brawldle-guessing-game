Created "answer sheet" containing brawler stats 👍
  - I narrowed the clue categories down to Brawler Number, Role, Rarity, Attack Range, Gender, Attacks per Ammo, and Super Type
  - Originally had movement speed, special traits, and species as potential clues, but ruled them out
  - If I think of a better category to have, I'll swap it out
  - There could be a few incorrect stats, so I'll go back through it to double check
  - Super Type is a fun column and prob my fav, but I'll have to figure out a way to make it display in a user-friendly way

---------------------------------------------------------------------------------
2) Create game logic for guessing 👍
- Made very crude logic for working game in python terminal, currently only tracks binary, yes or no
- Converted to OOP based guessin game, hopefully will translate to UI more easily
- Added higher/lower to brawler number and partial correct for super

- The general idea that I'm planning for this is that I basically have entirely backend logic in my code rn. Once I make frontend, it will just be interactable by client, then makes API calls to /src backend to return logic.
---------------------------------------------------------------------------------
3) Convert game logic from CLI -> servered backend (IP) 👍
- I decided to use Fast API since the backend is pretty lightweight
- Starting with just a GET home and POST guess
- Opted for using cookies to manage browser memory, to preserve guesses if someone closes the tab or smth. Also just more intuitive than looking up session id each time
---------------------------------------------------------------------------------
4) Create basic frontend/UI for game 👍
- Using ReactJS + Vite frontend, since that's what I'm familiar with
- It's a very light app, so the frontend isn't that deep
- Wired together frontend functions to make API calls
- Pretty satisfied with frontend ATP. Things I added:
- Found brawl stars theme and icons online, added those
- Added tile flipping like wordle, and minorly changed the way super type handles partial corrects
- Fixed some of the pngs and format stuff, then added tooltips on how to play, as well as my github at the bottom. Frontend should be good for now.
---------------------------------------------------------------------------------
5) Dockerize
- I'm going to split my frontend and backend into two different containers. Since they use completely different things, I think it'd be more organized just to do it that way.
---------------------------------------------------------------------------------
8) Secure app before deploying (IP)
- There are a few security things I'm going to have to fix before deploying, so I'll get to work on those
1) Expose port instead of mapping: listing port mappings in docker compose states how traffic to host is mapped to traffic to container. Having this mapping means someone could connect to the host port to talk directly to backend, so we hide this by exposing port instead of mapping (so it only allows traffic from inside the private network.)
2) Remove expired cookie sessions from memory: The way I had it before, all sessions are stored in memory (which is gonna be grow enormous). While cookies expire, the sessions still live in memory, so I made it so it terminates the sessions that have expired cookies since we don't need them anymore.
3) Add rate limiting to the guess path through frontend: Guess api takes a reasonable amount of computing power, so someone spamming it could mess us up pretty bad. We implement rate limiting on nginx taking requests from frontend.
4) Add rate limiting to the api directly. I did this with slowapi, so the backend has a hard limit on requests / min from a client.
5) Remove API docs from backend: Right now, if people find my backend port (which they shouldn't be able to do anyways), they can use the fastapi docs to see all my dev debug tools (/docs, /redoc, etc). In this case, it doesn't affect much, but it's good practice to hide these. 
6) Secure nginx server with security headers: Added a few headers that help avoid people griefing my site.
  1) X-Content-Type-Options "nosniff": makes it so that browser always uses content-type that nginx server sends instead of guessing
  2) X-Frame-Options "DENY": People can't hide a link to my website in their website's html
  3) Referrer-Policy "strict-origin-when-cross-origin": Hides potentially sensitive URL info when redirecting to a different website (shouldn't be a problem, but no loss in implemeting)
  4) Content Secure Policy: Prevents people from injecting into my website. Without this theoretically, someone could find out a way to inject html into the search bar and get it to display on my site. CSP outlines whether code will be loaded based on where it came from.
7) Make custom user for containers: Sort of like least-privelege perms, containers are given users who are allowed to interactive with just enough to build the containers. Without this, it defaults to root access, giving our container users access to the whole machine
8) Fix versions for requirements.txt: Without this, people could pip install different versions of these packages, which could change in the future.