# Import the required libraries. Unlike the QGIS Python console, in Python plugins we must explicitly import all dependencies.
from pathlib import Path
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.uic import loadUiType


# Load the UI definition from the .ui file. This generates a class we can use to create and manipulate the dialog widgets, such as input fields.
ExchangeRateDialogUi, _ = loadUiType(
    str(Path(__file__).with_name("exchange_rate_dialog.ui"))
)


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
        # Create an instance of our dialog and show it.
        self.exchange_rate_dialog = ExchangeRateDialog()
        self.exchange_rate_dialog.show()


# Create a dedicated class for our dialog, inheriting from both QDialog and the generated UI class. This allows us to manipulate the dialog widgets.
class ExchangeRateDialog(QDialog, ExchangeRateDialogUi):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the user interface and initialize all the widgets defined in the UI. The `setupUi` method is provided by the generated UI class `ExchangeRateDialogUi`.
        self.setupUi(self)
        # Set the title of the dialog window in the GUI, so we make the user aware what they are being shown.
        self.setWindowTitle("Currency Converter")
        # When the "Calculate" button is clicked, call the `_convert_currency` method.
        self.calculateButton.clicked.connect(self._convert_currency)

    # Method to perform the currency conversion when the button is clicked. For now we just create an empty method.
    def _convert_currency(self):
        # pass indicates an empty block of code. We will implement the conversion logic later.
        pass
