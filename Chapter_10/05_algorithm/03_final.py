# Import the required libraries.
# Unlike the QGIS Python console, in Python plugins we must explicitly import all dependencies.
from typing import Any, Optional

import urllib.parse
import json

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsNetworkAccessManager,
)
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest


# All Processing algorithms should extend the `QgsProcessingAlgorithm` class.
class ExchangeRateAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm adds a new attribute to a vector layer with the amount from another attribute converted to a different currency.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    INPUT_LAYER = "INPUT_LAYER"
    INPUT_FIELD = "INPUT_FIELD"
    INPUT_CURRENCY = "INPUT_CURRENCY"
    OUTPUT_CURRENCY = "OUTPUT_CURRENCY"
    OUTPUT_LAYER = "OUTPUT_LAYER"

    # The supported currencies for the conversion.
    # The list of currencies can be extended by adding more currency codes.
    SUPPORTED_CURRENCIES = ["eur", "usd", "gbp"]

    # Returns the algorithm name, used for identifying the algorithm.
    # This string should be fixed for the algorithm, and must not be localised.
    # The name should be unique.
    # Names should contain lowercase alphanumeric characters only and no spaces or other formatting characters.
    def name(self) -> str:
        return "currencyexchange"

    # Returns the translated algorithm name, which should be used for any user-visible display of the algorithm name.
    def displayName(self) -> str:
        return "Currency Exchange Attribute"

    # Returns the name of the group this algorithm belongs to.
    # This string should be localised.
    def group(self) -> str:
        return "My First Algorithms"

    # Returns the unique ID of the group this algorithm belongs to.
    # This string should be fixed for the algorithm, and must not be localised.
    # The group id should be unique.
    # Group id should contain lowercase alphanumeric characters only and no spaces or other formatting characters.
    def groupId(self) -> str:
        return "myfirstalgorithms"

    # Returns a localised short helper string for the algorithm.
    # This string should provide a basic description about what the algorithm does and the parameters and outputs associated with it.
    def shortHelpString(self) -> str:
        return "This algorithm adds a new attribute to a vector layer with the amount from another attribute converted to a different currency."

    # This method is called by QGIS to create a new instance of the algorithm class.
    def createInstance(self):
        return self.__class__()

    # Here we define the inputs and output of the algorithm, along with some other properties.
    def initAlgorithm(self, _config: Optional[dict[str, Any]] = None) -> None:
        # We add the input vector features source. It can have any kind of vector layer, even geometry-less.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                "Input layer",
                [QgsProcessing.SourceType.TypeVector],
            )
        )
        # Require the input field to be a numeric field from the selected layer.
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD,
                "Input amount field",
                type=QgsProcessingParameterField.Numeric,
                parentLayerParameterName=self.INPUT_LAYER,
                allowMultiple=False,
                defaultValue=None,
            )
        )
        # Add the input currency parameter with a list of supported currencies.
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_CURRENCY,
                "Input currency",
                options=self.SUPPORTED_CURRENCIES,
                allowMultiple=False,
                usesStaticStrings=False,
                defaultValue=[],
            )
        )
        # Add the output currency parameter with a list of supported currencies.
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OUTPUT_CURRENCY,
                "Output currency",
                options=self.SUPPORTED_CURRENCIES,
                allowMultiple=False,
                usesStaticStrings=False,
                defaultValue=[],
            )
        )
        # We add a feature sink in which to store our processed features (this usually takes the form of a newly created vector layer when the algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                "Output layer",
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the input layer as a feature source.
        input_layer = self.parameterAsSource(parameters, self.INPUT_LAYER, context)

        # If source was not found, throw an exception to indicate that the algorithm encountered a fatal error.
        # The exception text can be any string, but in this case we use the pre-built `invalidSourceError` method to return a standard helper text for when a source cannot be evaluated.
        if input_layer is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT_LAYER)
            )

        # Retrieve the input amount field.
        # This is the field that will be converted to a different currency.
        input_field_names = self.parameterAsFields(
            parameters, self.INPUT_FIELD, context
        )

        # The value is an array of field names, so we need to check if it is empty.
        if not input_field_names:
            raise QgsProcessingException("Invalid input amount field!")

        # Retrieve the input and output currency.
        # Note the values are the index of the selected currency in the list of supported currencies.
        input_currency_idx = self.parameterAsEnum(
            parameters, self.INPUT_CURRENCY, context
        )

        if input_currency_idx is None:
            raise QgsProcessingException("Invalid input currency!")

        output_currency_idx = self.parameterAsEnum(
            parameters, self.OUTPUT_CURRENCY, context
        )

        if output_currency_idx is None:
            raise QgsProcessingException("Invalid output currency!")

        # Get the currency codes from the selected currency indices.
        input_currency = self.SUPPORTED_CURRENCIES[input_currency_idx]
        output_currency = self.SUPPORTED_CURRENCIES[output_currency_idx]
        # Build the name of the output layer field that will store the converted amount.
        output_field_name = f"{input_field_names[0]}_{output_currency}"

        # Show some information to the user what is going to happen.
        feedback.pushInfo(
            f"Will convert from {input_currency} to {output_currency} and store it in {output_field_name}"
        )

        # Get the list of fields from the input layer.
        fields = input_layer.fields()

        # Add the new field to the list of fields.
        # If the field with such names already exists, throw an exception.
        if not fields.append(QgsField(output_field_name, QVariant.Double)):
            raise QgsProcessingException(f"Field {output_field_name} already exists!")

        # Instead of creating an output layer directly, we can use the output feature sink to add features.
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER,
            context,
            fields,
            input_layer.wkbType(),
            input_layer.sourceCrs(),
        )

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated.
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT_LAYER)
            )

        # Get the exchange rate from the input currency to the output currency.
        exchange_rate = self._getCurrencyExchangeRate(input_currency, output_currency)

        if exchange_rate is None:
            raise QgsProcessingException(
                f"Failed to get the exchange rate from {input_currency} to {output_currency}!"
            )

        feedback.pushInfo(
            f"The exchange rate from {input_currency} to {output_currency} is {exchange_rate}"
        )

        # Compute the number of steps to display within the progress bar and
        # get features from source.
        total_steps = (
            100.0 / input_layer.featureCount() if input_layer.featureCount() else 0
        )
        # Get an iterator of all features from the input layer.
        features = input_layer.getFeatures()

        for current_step, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked.
            if feedback.isCanceled():
                break

            # Get the value from the input field and convert it to the output currency amount.
            value = feature[input_field_names[0]] * exchange_rate

            # Copy the feature attributes and add the new value to the end.
            new_feature = QgsFeature(fields)
            new_feature.setGeometry(feature.geometry())
            new_feature.setAttributes(feature.attributes() + [value])

            # Add a feature in the sink.
            sink.addFeature(new_feature, QgsFeatureSink.Flag.FastInsert)

            # Update the progress bar.
            feedback.setProgress(int(current_step * total_steps))

        # Return the results of the algorithm. In this case our only result is the feature sink which contains the processed features,
        # but some algorithms may return multiple feature sinks, calculated numeric statistics, etc.
        # These should all be included in the returned dictionary, with keys matching the feature corresponding parameter or output names.
        return {self.OUTPUT_LAYER: dest_id}

    def _getCurrencyExchangeRate(
        self, input_currency: str, output_currency: str
    ) -> float | None:
        # Try if we can get the exchange rate from the internet API.
        try:
            exchange_rates = get_exchange_rates(input_currency)

            # Check if the output currency is in the returned exchange rates.
            if (
                input_currency in exchange_rates
                and output_currency in exchange_rates[input_currency]
            ):
                return exchange_rates[input_currency][output_currency]
            else:
                self.pushInfo("Cannot find exchange rate for the given currencies!")

                return None
        except Exception as err:
            self.pushInfo(f"Failed to download exchange rates: {err}")

            return None


def get_exchange_rates(input_currency: str) -> dict[str, dict[str, float]]:
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
