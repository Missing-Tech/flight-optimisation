from pycontrails.models.issr import ISSR
import ecmwf
from pycontrails.models.humidity_scaling import ConstantHumidityScaling

params = {
    "humidity_scaling": ConstantHumidityScaling(rhi_adj=0.98),
}

issr_mds = ISSR(ecmwf.met, params=params).eval()
issr = issr_mds["issr"]
# issr_edges = issr.find_edges()

da = issr.data.isel(level=0).isel(time=0).to_dataframe().reset_index()
# da = da[da["issr"] > 0]
