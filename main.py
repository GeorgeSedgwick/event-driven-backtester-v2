from research.walk_forward import run_walk_forward
from research.benchmarking import compare_to_benchmark




if __name__ == "__main__":
    MODE = "benchmark" # "walkforward" | "benchmark"
    
    if MODE == "walkforward":
        run_walk_forward()

    elif MODE == "benchmark":
        compare_to_benchmark()







