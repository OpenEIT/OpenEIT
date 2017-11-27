# EIT_Dashboard
Dashboard for real-time EIT processing and image reconstruction using filtered linear back-projection.

python dashboard.py runs everything. 

If you don't have any of the dependencies installed you should get an error, otherwise the dashboard GUI should be ready to use. 

![alt text](images/dashboard.png "EIT Dashboard")

![alt text](images/eit_anti-clockwise_motion.png "EIT and how it should appear")

Snake Viz General Instructions: 
==================================

Snakeviz Code Profiling instructions: 

pip install snakeviz 

Generate a cProfile: 
python -m cProfile -o program.prof my_program.py

Interpret results:  
snakeviz program.prof

![alt text](images/snakeviz.png "Snake Viz Code Profiler")


