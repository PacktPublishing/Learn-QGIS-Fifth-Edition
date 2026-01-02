from qgis.utils import iface
from qgis.core import Qgis

# this macros will run every time a project is saved
def saveProject():
    # to the QIGS message bar, add a new message
    iface.messageBar().pushMessage(
            "Warning",
            "This project contains top secret ice-cream locations! Keep the project and its data secret!",
            Qgis.Warning,
            10
    )

