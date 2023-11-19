import cdsapi

c = cdsapi.Client()

c.retrieve(
    "reanalysis-era5-complete",
    {
        "class": "ea",
        "date": "2023-03-31",
        "expver": "1",
        "levelist": "200/225/250/300",
        "levtype": "pl",
        "param": "130.128/131/132/157.128",
        "step": "0",
        "stream": "oper",
        "time": "09:00:00",
        "grid": "0.25/0.25",
        "type": "4v",
    },
    "output",
)
