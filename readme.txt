
General Instructions: 

python dashboard.py runs everything. 

Snakeviz Code Profiling instructions: 

pip install snakeviz 

Generate a cProfile: 
python -m cProfile -o program.prof my_program.py

Interpret results:  
snakeviz program.prof