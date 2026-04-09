def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to the project."
def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
