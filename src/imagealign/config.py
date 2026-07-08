from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class ObjectConfig:
    name: str
    ra: str
    dec: str

@dataclass
class CCDConfig:
    gain: float
    rmnoise: float
    pxscale: float
    naxis1: int
    naxis2: int
    datamax: int

@dataclass
class Align:
    method: str
    resample: str
    resampling_type: str
    subtract_background: str
    resample_suffix: str
    pixel_scale_type: str

@dataclass
class Combine:
    coadd: str
    combine_type: str
    coadded_suffix: str

@dataclass
class ConfigurationSetup:
    config_sex: str
    param_sex: str
    config_scamp: str
    config_swarp: str

@dataclass
class Config:
    object: ObjectConfig
    ccd : CCDConfig
    align: Align
    combine: Combine
    configuration_setup: ConfigurationSetup
    working_dir: Path

def load_config(config_file: str) -> Config:

    with open(config_file) as f:
        data = yaml.safe_load(f)


    return Config(
        object=ObjectConfig(**data['object']),
        ccd=CCDConfig(**data['ccd']),
        align=Align(**data['alignment']),
        combine=Combine(**data['combine']),
        configuration_setup=ConfigurationSetup(**data['configuration']),
        working_dir=Path(data["working_dir"]),
    )

