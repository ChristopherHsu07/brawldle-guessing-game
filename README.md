# Brawldle: Brawl Stars Guessing Game

<img width="1071" height="594" alt="Screenshot 2026-08-05 at 10 40 26 PM" src="https://github.com/user-attachments/assets/fd260e26-b876-446b-b3a0-491faab142c1" />

## Do you like Brawl Stars? Try out this Wordle-inspired Brawl Stars Guessing Game!

Using a React.js + Vite frontend and a simple FastAPI backend, I made a game where you try to guess the brawler based on categories

# HOW TO PLAY:
Start by guessing a brawler, where you'll see several categories pop up, including brawler number, gender, attack range, etc. From these, You will see which ones are correct, partially correct, or incorrect, narrowing the possible brawler. Try to guess the brawler in as few guesses as possible!

# HOW TO RUN IT:
You can either run the project on your machine or run it on Docker. 


## RUNNING ON DOCKER (RECOMMENDED)
1) Make sure you have Docker installed
2) Clone the project with
```bash
git clone https://github.com/ChristopherHsu07/brawldle-guessing-game.git
```
3) From the root, build and run the containers with 
```bash
docker compose up --build
```
Frontend will default to run on localhost port 80.

## RUNNING LOCALLY
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
pip install requirements.txt
```
Run backend:
```bash
uvicorn src.api:app --reload
```
cd into frontend, the run frontend:
```bash
cd ../frontend
npm run dev
```
Frontend will default to running on port 5173.

## COMMENTS
- Brawler stats/data can sometimes be incorrect, so please let me know if you see anything about brawlers that is wrong!
- CSS/design is modeled from Aina Raharison, found [here](https://codepen.io/aina-raharison/pen/wvdaqbV)