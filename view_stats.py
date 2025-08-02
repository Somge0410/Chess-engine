import pstats

# Load the stats file
stats = pstats.Stats('my_profile_stats.prof')

# Sort the stats by cumulative time and print the top 25 results
stats.sort_stats('cumulative').print_stats(30)

# Or, sort by total time spent inside a function and print the top 25
# stats.sort_stats('tottime').print_stats(25)
#python -m cProfile -o my_profile_stats.prof main.py