"""
Run the whole audit in order. Usage:
  PLAYMAKER_PDF=/path/to/Playmaker_Rating_System_and_Player_Ratings.pdf python3 run_all.py
Steps: ingest (PDF -> data/cards.csv), validate, outcome tables, audit, what-ifs, prototype check.
"""
import audit
import ingest
import matchups
import prototype
import validate
import whatif

if __name__ == "__main__":
    for step in (ingest, validate, matchups, audit, whatif, prototype):
        print(f"\n===== {step.__name__} =====")
        step.main()
