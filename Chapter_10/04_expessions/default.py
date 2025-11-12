# first import the required decorator
from qgis.core import qgsfunction

# now define the function using the decorator and it's expressions group name
@qgsfunction(group="QGIS Book")
def fahrenheit_to_celsius(fahrenheit: float) -> float:
    celsius = (fahrenheit - 32) * 5 / 9
    return celsius
