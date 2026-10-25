"""Fitted capture, scaled by wallet: exact positive wallet homogeneity."""
import numpy as np
from scipy.special import expit,logit
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from ml.training.reference_sales.features import FEATURES
from ml.training.reference_sales.models import preprocessor

CAPTURE_FEATURES=tuple(f for f in FEATURES if f!='annual_wallet_inr')

class CaptureModel:
    def __init__(self,family,parameters,seed,features=CAPTURE_FEATURES):
        self.family=family;self.parameters=parameters;self.seed=seed;self.features=tuple(features)
    def fit(self,x,y):
        share=np.asarray(y)/x.annual_wallet_inr.to_numpy()
        if not np.all((share>0)&(share<1)):raise ValueError('Training shares must be strictly inside (0,1); no target clipping')
        self.preprocessor=preprocessor(self.features);design=self.preprocessor.fit_transform(x[list(self.features)])
        self.fit_rows=len(x)
        if self.family=='median':self.estimator=DummyRegressor(strategy='median')
        elif self.family=='ridge':self.estimator=Ridge(**self.parameters)
        elif self.family=='catboost':
            from catboost import CatBoostRegressor
            self.estimator=CatBoostRegressor(**self.parameters,random_seed=self.seed,thread_count=1,task_type='CPU',loss_function='RMSE',verbose=False,allow_writing_files=False)
        else:raise ValueError('Unknown model family')
        self.estimator.fit(design,logit(share));return self
    def share(self,x):return expit(self.estimator.predict(self.preprocessor.transform(x[list(self.features)])))
    def predict(self,x):return self.share(x)*x.annual_wallet_inr.to_numpy(float)
