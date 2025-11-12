# This is sample python to be ran in the Python Console of QGIS.
# Ignroe all the lines that are prefixes with #, they are Python comments and do not have any effect in Python.

# Print the current QGIS version.
print(Qgis.version())


# Expression that prints the current QGIS version concatenated with a prefix.
"QGIS version is:" + Qgis.version()


# Print the current active layer. Note that it might return `None` if the current project has no layers or there is no selected layer. (step 4)
iface.activeLayer()


# Get help for unknown data type, in this case `QgsVectorLayer`.
help(QgsVectorLayer)


# Assuming there is a selected layer in our current project, let's get the layer name. (step 5)
iface.activeLayer().name()


# Instead of writing the whole expression every time, let's store the current active vector layer in a variable. (step 6)
vl = iface.activeLayer()


# Get the names of the fields of the current vector layer. (step 7)
vl.fields().names()


# Calculate the average income for all features. (step 8)
# first for each feature in the layer, get all the values of Sales_USD that has a positive value (ignore nulls)
all_income = [f.attribute("Sales_USD") for f in vl.getFeatures() if f.attribute("Sales_USD") > 0]
# then sum those values
total_income = sum(all_income)
# then count how many values we had
count = len(all_income)
# calculate the average
avg_income = total_income / count
# print the result
print("Total income is", total_income, "or", avg_income, "on average for", count, "locations.")


# Search for layer by name in the current project. Note the result is a list of layer objects.
QgsProject.instance().mapLayersByName("locations")
# assuming there is a layer called "locations" in the current QGIS project, store the layer reference in a variable `vl`.
vl = QgsProject.instance().mapLayersByName("locations")[0]


