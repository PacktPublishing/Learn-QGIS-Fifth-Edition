# Import the required libraries.
# Unlike the QGIS Python console, in Python plugins we must explicitly import all dependencies.
import json
import urllib.parse
from pathlib import Path

from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtGui import QIcon


ExchangeRateDialogUi, _ = loadUiType(
    str(Path(__file__).with_name("exchange_rate_dialog.ui"))
)


def get_exchange_rate(input_currency: str) -> dict[str, dict[str, float]]:
    """Get the exchange rates for a given currency code.

    Args:
        input_currency: The currency code to get the exchange rates for.

    Returns:
        A dictionary with the exchange rates for the given currency code. Formatted as follows:
        { <input_currency>: { <output_currency>: <exchange_rate>, ... }, ... }
    """
    # The API requires the currency code to be URL-encoded.
    currency_code_quoted = urllib.parse.quote(input_currency.lower())
    # The API URL is constructed by appending the URL-encoded currency code to the base URL.
    # There are multiple exchange rate providers, this is by far one of the easiest to use.
    url = f"https://latest.currency-api.pages.dev/v1/currencies/{currency_code_quoted}.json"

    # The `QgsNetworkAccessManager.blockingGet` function is a convenience function that performs a blocking HTTP GET request.
    # While it is not recommended to use blocking functions in the main thread, it is acceptable for simple plugins.
    # It greatly simplifies the code and makes it easier to understand.
    response = QgsNetworkAccessManager.blockingGet(QNetworkRequest(QUrl(url)))
    # Explicitly convert to bytes from QBytesArray to avoid issues with JSON parsing.
    raw_content = bytes(response.content())
    # The response is a JSON string, so we need to parse it into a Python dictionary.
    content = json.loads(raw_content)

    return content


# This function is required by the QGIS plugin framework to actually instantiate a QGIS plugin.
# It takes an instance of `QgisInterface` as a parameter and expects an instance of a class implementing `initGui` and `unload` methods.
def classFactory(iface):
    return QgisBookMinimalPlugin(iface)


# The class that defines our plugin functionality.
class QgisBookMinimalPlugin:
    # The constructor of the plugin stores a reference to the `QgisInterface` instance.
    def __init__(self, iface):
        self.iface = iface

    # Mandatory method to initialize the Graphical User Interface (GUI) of the plugin.
    # In our case the GUI is a single button on the toolbar.
    def initGui(self):
        # Create a new action.
        self.action = QAction("QGIS book minimal plugin", self.iface.mainWindow())
        # Set the icon of the action. Note we build the full path to the file
        self.action.setIcon(QIcon(str(Path(__file__).with_name("icon.svg"))))
        # Define what happens when it is triggered. In this case we will call the `on_triggered` function.
        self.action.triggered.connect(self._on_action_triggered)
        # Add the action to the QGIS interface toolbar.
        self.iface.addToolBarIcon(self.action)

    # Mandatory method to de-initialize the GUI.
    # Called when the plugin is disabled or removed from QGIS.
    def unload(self):
        # Since we added the plugin action in `initGui` to the QGIS interface toolbar, we need to clean-up after ourselves and remove it.
        self.iface.removeToolBarIcon(self.action)

    # Custom method with name decided by us.
    # The name suggests it will only execute when the action we defined in `initGui` is triggered.
    def _on_action_triggered(self):
        # Create a new instance of the `ExchangeRateDialog` class.
        self.exchange_rate_dialog = ExchangeRateDialog()
        # Show the dialog window.
        self.exchange_rate_dialog.show()


class ExchangeRateDialog(QDialog, ExchangeRateDialogUi):  #  type: ignore
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        # Set the title of the dialog window in the GUI, so we make the user aware what they are being shown.
        self.setWindowTitle("Currency Converter")
        # When the "Calculate" button is clicked, call the `_convert_currency` method.
        self.calculateButton.clicked.connect(self._convert_currency)

    def _convert_currency(self):
        # Get the input amount, input currency, and output currency from the dialog.
        # We are accessing the instances of the widgets defined in the `exchange_rate_dialog.ui` file in Qt Designer.
        # Note that the different widget types have different methods to get their values.
        input_amount = self.inputAmount.value()
        input_currency = self.inputCurrency.currentText()
        output_currency = self.outputCurrency.currentText()

        # Get the exchange rates for the input currency.
        # Since we are connecting to an online resource there is a chance that the request will fail.
        # We should handle this case and show an error message.
        try:
            exchange_rates = get_exchange_rate(input_currency)
            # Get the exchange rate for the output currency.
            exchange_rate = exchange_rates[input_currency][output_currency]
            # Calculate the output amount by multiplying the input amount by the exchange rate.
            output_amount = input_amount * exchange_rate
            # Update the output amount in the GUI.
            self._set_output_amount(output_amount)
        # Instead of breaking the program when something goes wrong, we catch the exception and show an error message.
        except Exception as err:
            # Show an error message box dialog with the error message.
            QMessageBox.critical(
                # The parent of the message box dialog, in this case the current `ExchangeRateDialog`.
                # Just pass `self` most of the time.
                self,
                # The title of the error message dialog.
                # By calling `self.tr` we are using the translation system of Qt.
                # Even though we are not translating the strings, it is a good practice to use from the beginning.
                self.tr("Currency exchange rate failed"),
                # The content of the error message dialog.
                # We append the dynamic error message in the end of the string.
                self.tr("Currency exchange rate error: ") + str(err),
            )
            # Setting the output amount to `None` will display "N/A" in the GUI.
            self._set_output_amount(None)

    def _set_output_amount(self, amount: float | None) -> None:
        # If the passed amount is `None`, we display "N/A" in the GUI.
        if amount is None:
            amount_str = self.tr("N/A")
        else:
            amount_str = str(amount)

        # Set the output amount in the GUI.
        # Since we are using a QLabel widget, we need to convert the amount to a string before setting it.
        self.outputAmount.setText(amount_str)
