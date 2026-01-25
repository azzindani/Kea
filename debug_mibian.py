
import mibian

def debug_mibian():
    print("Mibian attributes:")
    print(dir(mibian))
    
    c = mibian.BS([100, 100, 5, 30], volatility=20)
    print("\nBS Object attributes:")
    print(dir(c))

if __name__ == "__main__":
    debug_mibian()
