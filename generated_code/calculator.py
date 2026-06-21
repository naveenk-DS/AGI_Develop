def add(x, y):
    """Return the sum of x and y."""
    return x + y

def subtract(x, y):
    """Return the difference of x and y."""
    return x - y

def multiply(x, y):
    """Return the product of x and y."""
    return x * y

def divide(x, y):
    """Return the division of x by y. Raise error if y is zero."""
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y

# Main calculator function
def calculator():
    """
    Simple command-line calculator.
    Supports addition, subtraction, multiplication, and division.
    """
    print("Select operation:")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")

    choice = input("Enter choice (1/2/3/4): ")

    if choice in ('1', '2', '3', '4'):
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))

        if choice == '1':
            print(f"{num1} + {num2} = {add(num1, num2)}")
        elif choice == '2':
            print(f"{num1} - {num2} = {subtract(num1, num2)}")
        elif choice == '3':
            print(f"{num1} * {num2} = {multiply(num1, num2)}")
        elif choice == '4':
            try:
                result = divide(num1, num2)
                print(f"{num1} / {num2} = {result}")
            except ValueError as e:
                print(e)
    else:
        print("Invalid input")

if __name__ == "__main__":
    calculator()