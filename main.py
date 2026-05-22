from research.walk_forward import run_walk_forward
from research.benchmarking import compare_to_benchmark
from research.wfo import run_wfo



if __name__ == "__main__":
    MODE = "wfo" # "benchmark" | "wfo"
    
    if MODE == "benchmark":
        compare_to_benchmark()

    elif MODE == "wfo":
        run_wfo()







