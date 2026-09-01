import pandas as pd, numpy as np
from scipy.stats import ttest_ind, chi2_contingency
KULA_ACCOUNTS = ['3-1-robot', '3-1-robot2']

def prepare(frame):
    x = frame.loc[frame['currentAccount'].isin(KULA_ACCOUNTS)].copy()
    x['score_num'] = pd.to_numeric(x['score'], errors='coerce')
    x['rated'] = x['score_num'].between(1, 5)
    x['good_survey'] = x['score_num'].isin([3,4,5])
    x['bad_survey'] = x['score_num'].isin([1,2])
    x['datetime'] = pd.to_datetime(x['createTime'], errors='coerce')
    x['date'] = x['datetime'].dt.date
    return x

june_files = [
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788146480 (1-5 june).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788146837 (6-10 june).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788148372 (11-15 june).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788149085 (16-20 june).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788149522 (21-25 june).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788150625 (26-30 june).csv']
aug_files = [
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788145507 (1-5 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788145209 (6-10 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788144961 (11-14 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1787219325 (13-15 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1787025549 (16-18 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1787219503 (19-20 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788144629 (21-26 aug).csv',
'../dataset_wellbore/akulaku_superset_presto_hanmm_ozy.prazuganda_1788141789 (27-31 aug).csv']

df_june = pd.concat([pd.read_csv(f, low_memory=False) for f in june_files], ignore_index=True).drop_duplicates(subset='id')
df_aug = pd.concat([pd.read_csv(f, low_memory=False) for f in aug_files], ignore_index=True).drop_duplicates(subset='id')

june = prepare(df_june)
aug = prepare(df_aug)
aug_last = df_aug.assign(datetime=pd.to_datetime(df_aug['createTime'], errors='coerce')).groupby(pd.to_datetime(df_aug['createTime'], errors='coerce').dt.date)['datetime'].max()
complete = aug_last.loc[aug_last.dt.hour.ge(23)].index
aug = aug.loc[aug['date'].isin(complete)].copy()

june_r = june.loc[june['rated']].copy(); aug_r = aug.loc[aug['rated']].copy()
print('June_valid_respondents', len(june_r))
print('August_valid_respondents', len(aug_r))
print('June_good_rate_pct', round(100*june_r['good_survey'].mean(), 4))
print('August_good_rate_pct', round(100*aug_r['good_survey'].mean(), 4))
print('June_bad_rate_pct', round(100*june_r['bad_survey'].mean(), 4))
print('August_bad_rate_pct', round(100*aug_r['bad_survey'].mean(), 4))
print('June_mean_score', round(june_r['score_num'].mean(), 4))
print('August_mean_score', round(aug_r['score_num'].mean(), 4))
print('CSAT_p', round(ttest_ind(june_r['score_num'], aug_r['score_num'], equal_var=False).pvalue, 4))
for col in ['good_survey','bad_survey']:
    tab = np.array([[june_r[col].sum(), (~june_r[col]).sum()], [aug_r[col].sum(), (~aug_r[col]).sum()]])
    print(col+'_p', round(chi2_contingency(tab, correction=False).pvalue, 4))
print('June_unique_users_per_day', round(june.groupby('date')['userId'].nunique().mean(), 2))
print('August_unique_users_per_day', round(aug.groupby('date')['userId'].nunique().mean(), 2))
print('June_raw_rows_per_day', round(june.groupby('date').size().mean(), 2))
print('August_raw_rows_per_day', round(aug.groupby('date').size().mean(), 2))
print('Raw_rows_delta_pct', round((aug.groupby('date').size().mean() / june.groupby('date').size().mean() - 1) * 100, 2))
print('Unique_users_delta_pct', round((aug.groupby('date')['userId'].nunique().mean() / june.groupby('date')['userId'].nunique().mean() - 1) * 100, 2))
