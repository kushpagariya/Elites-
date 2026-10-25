"""Train-only preprocessing and fitted, wallet-bounded annual-sales heads."""
from dataclasses import dataclass, field
import numpy as np
from scipy.special import expit, logit
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from .features import FEATURES, NUMERIC


def preprocessor(features):
    numeric=[f for f in features if f in NUMERIC]
    return ColumnTransformer([
        ('numeric',Pipeline([
            ('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
            ('log1p',FunctionTransformer(np.log1p,feature_names_out='one-to-one')),
            ('scale',StandardScaler()),
        ]),numeric),
        ('format',OneHotEncoder(handle_unknown='error',sparse_output=False),['store_format']),
    ],remainder='drop',verbose_feature_names_out=True)


@dataclass
class BoundedSalesModel:
    name: str
    parameters: dict
    seed: int
    features: tuple=FEATURES
    transformer: object=field(default=None,init=False)
    estimator: object=field(default=None,init=False)
    fit_row_count: int=field(default=0,init=False)

    def fit(self,x,y):
        if list(x.columns)!=list(self.features):raise ValueError('Training columns differ from versioned allowlist')
        y=np.asarray(y,dtype=float);wallet=x['annual_wallet_inr'].to_numpy(float)
        if np.any(~np.isfinite(y)) or np.any(y<0) or np.any(y>wallet+1e-6):raise ValueError('Target violates physical spending bound')
        self.fit_row_count=len(x)
        if self.name=='median':
            self.estimator=DummyRegressor(strategy='median').fit(np.zeros((len(x),1)),y)
            return self
        self.transformer=preprocessor(self.features)
        xx=self.transformer.fit_transform(x)
        # Both fitted regressors learn log-odds of capture; the output head maps
        # back to annual INR using the observed input wallet. This is a bounded
        # target parameterisation, not an observed-sales calibration.
        fraction=np.divide(y,wallet,out=np.zeros_like(y),where=wallet>0)
        z=logit(np.clip(fraction,1e-8,1-1e-8))
        if self.name=='ridge':
            self.estimator=Ridge(**self.parameters)
        elif self.name=='catboost':
            from catboost import CatBoostRegressor
            self.estimator=CatBoostRegressor(**self.parameters,random_seed=self.seed,
                thread_count=1,task_type='CPU',loss_function='RMSE',allow_writing_files=False,verbose=False)
        else:raise ValueError('Unsupported fitted model '+self.name)
        self.estimator.fit(xx,z)
        return self

    def predict(self,x):
        if list(x.columns)!=list(self.features):raise ValueError('Inference columns differ from training schema')
        wallet=x['annual_wallet_inr'].to_numpy(float)
        if self.name=='median':pred=self.estimator.predict(np.zeros((len(x),1)))
        else:pred=expit(self.estimator.predict(self.transformer.transform(x)))*wallet
        if np.any(~np.isfinite(pred)):raise ValueError('Nonfinite fitted prediction')
        return np.clip(pred,0,wallet)


def preprocessing_record(model):
    if model.transformer is None:
        return dict(kind='NO_FEATURE_TRANSFORM_MEDIAN_BASELINE',fit_row_count=model.fit_row_count)
    numeric=model.transformer.named_transformers_['numeric']
    imputer=numeric.named_steps['impute'];scaler=numeric.named_steps['scale']
    return dict(kind='TRAIN_ONLY_MEDIAN_INDICATOR_LOG1P_STANDARD_SCALE_AND_FORMAT_ONE_HOT',
        fit_row_count=model.fit_row_count,transformed_feature_names=model.transformer.get_feature_names_out().tolist(),
        imputation_statistics=imputer.statistics_.tolist(),missing_indicator_indices=imputer.indicator_.features_.tolist(),
        scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),
        format_categories=[a.tolist() for a in model.transformer.named_transformers_['format'].categories_],
        target_transform='logit(capture fraction clipped to [1e-8,1-1e-8]); inference expit * input annual_wallet_inr',
        no_imputation_of_unavailable_routing_or_households=True)
