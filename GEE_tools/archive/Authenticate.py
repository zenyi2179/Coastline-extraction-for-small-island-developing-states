import ee

try:
    ee.Initialize()
except ee.EEException:
    ee.Authenticate()
    ee.Initialize()