"""Versioned input allowlist. No target, own branches or financial-cost inputs."""
from collections.abc import Mapping, Sequence
from numbers import Real
import math

import numpy as np
import pandas as pd

SCHEMA_VERSION = 'reference-sales-features-v1'
DAYPART = (
    'weekday_morning_raw', 'weekday_lunch_raw', 'weekday_evening_raw',
    'weekday_night_raw', 'weekend_day_raw', 'weekend_evening_raw',
)
POIS = (
    'office_poi_count_1500m', 'education_poi_count_1500m',
    'healthcare_poi_count_1500m', 'transit_poi_count_1500m',
    'shopping_poi_count_1500m', 'food_leisure_poi_count_1500m',
)
NUMERIC = (
    'store_size_sqm', 'annual_wallet_inr', 'population_1500m_est',
    'competitor_count_1500m', 'competitor_attraction_index',
    'nearest_competitor_distance_m', 'mean_wallet_weighted_distance_m',
) + POIS + DAYPART
FEATURES = NUMERIC + ('store_format',)
TARGET = 'reference_annual_sales_inr'
FORMATS = ('supermarket', 'grocery', 'convenience')
COUNTS = set(POIS) | {'competitor_count_1500m'}
NULLABLE = {'nearest_competitor_distance_m'}
UNITS = {k:('mapped POI count' if k in COUNTS else 'relative opportunity per nominal hour' if k in DAYPART else 'INR/year nominal wallet basis' if k=='annual_wallet_inr' else 'estimated persons' if k=='population_1500m_est' else 'square metres' if k=='store_size_sqm' else 'metres' if k.endswith('_m') else 'dimensionless relative attraction') for k in NUMERIC}
UNITS['store_format']='format category'


class FeatureValidationError(ValueError):
    """Prepared source features are absent, invalid or schema-incompatible."""


def feature_frame(rows: Sequence[Mapping], features=FEATURES, allowed_extra=(), allow_csv_strings=False):
    """Select named features, rejecting invented/missing values.

    Empty/None nearest distance is meaningful only when mapped competitors=0.
    A trained imputer handles that declared undefined distance; no missing
    routing/household fields are manufactured. CSV string conversion is explicit.
    """
    clean=[]
    for i,row in enumerate(rows):
        if not isinstance(row,Mapping):
            raise FeatureValidationError(f'Row {i} must be a prepared feature mapping')
        missing=set(features)-set(row)
        unknown=set(row)-set(features)-set(allowed_extra)
        if missing or unknown:
            raise FeatureValidationError(f'Row {i}: missing={sorted(missing)}, unknown={sorted(unknown)}')
        values={}
        for field in features:
            value=row[field]
            if field=='store_format':
                if value not in FORMATS:raise FeatureValidationError(f'Unsupported store_format: {value!r}')
                values[field]=value
                continue
            if value is None or (isinstance(value,str) and value=='') or (isinstance(value,Real) and math.isnan(float(value))):
                if field not in NULLABLE:raise FeatureValidationError(f'Row {i}: missing required {field}')
                values[field]=np.nan
                continue
            if isinstance(value,(bool,np.bool_)) or (isinstance(value,str) and not allow_csv_strings) or not isinstance(value,(Real,str)):
                raise FeatureValidationError(f'Row {i}: {field} must be a finite number')
            try:number=float(value)
            except (TypeError,ValueError) as exc:raise FeatureValidationError(f'Row {i}: invalid {field}') from exc
            if not math.isfinite(number) or number<0:raise FeatureValidationError(f'Row {i}: invalid nonnegative {field}')
            if field=='store_size_sqm' and number==0:raise FeatureValidationError('store_size_sqm must be positive')
            if field in COUNTS and not number.is_integer():raise FeatureValidationError(f'{field} must be an integer count')
            if field.endswith('_distance_m') and number>1500+1e-6:raise FeatureValidationError(f'{field} exceeds declared 1500m catchment')
            values[field]=number
        count=values.get('competitor_count_1500m')
        nearest=values.get('nearest_competitor_distance_m')
        if nearest is not None and (math.isnan(nearest)!=(count==0)):
            raise FeatureValidationError('Nearest competitor distance is null exactly when mapped competitor count is zero')
        if values.get('competitor_attraction_index',0)>count+1e-6:
            raise FeatureValidationError('Equal-unit mapped attraction exceeds competitor count')
        clean.append(values)
    return pd.DataFrame(clean,columns=list(features))


def feature_schema(canonical_columns):
    return dict(schema_version=SCHEMA_VERSION,feature_allowlist=list(FEATURES),
        canonical_input_columns=list(canonical_columns),
        logical_types={k:'String' if k=='store_format' else 'Int64' if k in COUNTS else 'Float64' for k in FEATURES},
        units=UNITS,nullable=sorted(NULLABLE),store_formats=list(FORMATS),
        missing_policy='Only nearest competitor distance may be undefined, with zero mapped competitors. Train-only median plus missingness indicator; no routing/household imputation.',
        target=TARGET,target_units='INR/year reference sales, before own-company displacement',
        source='Prepared canonical Bengaluru feature names; no Bengaluru outcomes or candidate rows enter simulator fitting')
