#  [Brawldle](https://brawldle-guessing-game.vercel.app "Try It Out!"): Brawl Stars Guessing Game

<img width="1071" height="594" alt="Screenshot 2026-08-05 at 10 40 26 PM" src="https://github.com/user-attachments/assets/fd260e26-b876-446b-b3a0-491faab142c1" />

## Do you like Brawl Stars? Try out this Wordle-inspired Brawl Stars Guessing Game!

Using a React.js + Vite frontend and a simple FastAPI backend with a Redis db, I made a game where you try to guess the brawler based on categories.

I deployed using Render for my backend and db, and Vercel for my frontend. If you want to see my progress and how I built it, check out PROGRESS.md.

# HOW TO PLAY:
Start by guessing a brawler, where you'll see several categories pop up, including brawler number, gender, attack range, etc. From these, You will see which ones are correct, partially correct, or incorrect, narrowing the possible brawler. Try to guess the brawler in as few guesses as possible!

# HOW TO RUN IT:

1) Clone the project with
```bash
git clone https://github.com/ChristopherHsu07/brawldle-guessing-game.git
```

From here, you can either run the project on your machine or run it on Docker. 

## RUNNING ON DOCKER (RECOMMENDED)
1) Make sure you have Docker installed
2) From the root, build and run the containers with 
```bash
docker compose up --build
```
Frontend will default to run on localhost port 80. This path starts Redis because Compose sets `REDIS_URL`.

## RUNNING LOCALLY
Local uvicorn does not need Redis; sessions stay in memory unless `REDIS_URL` is set (Docker and Render set it).

1) Make sure you have Node.js installed
2) cd into frontend folder, then install frontend requirements:
```bash
cd frontend
npm install
```
cd back to root, then into backend folder and create a virtual environment, then install backend requirements:
```bash
cd ../backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Run backend (from the backend folder). Skip `--reload` by default — on macOS it can hang during pandas import and never accept requests:
```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000
```
Optional auto-reload if that works on your machine: `uvicorn src.api:app --reload --host 127.0.0.1 --port 8000`.

cd into frontend, then run frontend:
```bash
cd ../frontend
npm run dev
```
Frontend will default to running on port 5173.

## COMMENTS
- Brawler stats/data can sometimes be incorrect, so please let me know if you see anything about brawlers that is wrong!
- CSS/design is modeled from Aina Raharison, found [here](https://codepen.io/aina-raharison/pen/wvdaqbV)